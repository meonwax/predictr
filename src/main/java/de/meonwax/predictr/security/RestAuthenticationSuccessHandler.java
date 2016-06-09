package de.meonwax.predictr.security;

import java.io.IOException;
import java.time.ZonedDateTime;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.Authentication;
import org.springframework.security.web.authentication.SimpleUrlAuthenticationSuccessHandler;
import org.springframework.stereotype.Component;

import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.repository.UserRepository;

@Component
public class RestAuthenticationSuccessHandler extends SimpleUrlAuthenticationSuccessHandler {

    private final Logger log = LoggerFactory.getLogger(RestAuthenticationSuccessHandler.class);

    @Autowired
    private UserRepository userRepository;

    @Override
    public void onAuthenticationSuccess(HttpServletRequest request, HttpServletResponse response, Authentication authentication) throws IOException, ServletException {

        String email = authentication != null ? authentication.getName() : "unknown";
        log.info("User logged in: " + email);

        clearAuthenticationAttributes(request);

        // Update last login time
        User user = userRepository.findOneByEmailIgnoringCase(email);
        if (user != null) {
            user.setLastLoginDate(ZonedDateTime.now());
            userRepository.save(user);
        }
    }
}
