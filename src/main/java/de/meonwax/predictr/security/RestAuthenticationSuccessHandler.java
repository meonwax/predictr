package de.meonwax.predictr.security;

import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.repository.UserRepository;
import lombok.AllArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.core.Authentication;
import org.springframework.security.web.authentication.SimpleUrlAuthenticationSuccessHandler;
import org.springframework.stereotype.Component;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.time.ZonedDateTime;

@Component
@AllArgsConstructor
public class RestAuthenticationSuccessHandler extends SimpleUrlAuthenticationSuccessHandler {

    private static final Logger LOGGER = LoggerFactory.getLogger(RestAuthenticationSuccessHandler.class);

    private final UserRepository userRepository;

    @Override
    public void onAuthenticationSuccess(HttpServletRequest request, HttpServletResponse response, Authentication authentication) {

        String email = authentication != null ? authentication.getName() : "unknown";
        LOGGER.info("User logged in: {}", email);

        clearAuthenticationAttributes(request);

        // Update last login time
        User user = userRepository.findOneByEmailIgnoringCase(email);
        if (user != null) {
            user.setLastLoginDate(ZonedDateTime.now());
            userRepository.save(user);
        }
    }
}
