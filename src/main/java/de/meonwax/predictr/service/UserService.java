package de.meonwax.predictr.service;

import de.meonwax.predictr.domain.Config;
import de.meonwax.predictr.domain.PasswordResetToken;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.dto.PasswordDto;
import de.meonwax.predictr.dto.UserDataDto;
import de.meonwax.predictr.dto.UserDto;
import de.meonwax.predictr.exception.PasswordResetException;
import de.meonwax.predictr.repository.PasswordResetTokenRepository;
import de.meonwax.predictr.repository.UserRepository;
import de.meonwax.predictr.util.PasswordGenerator;
import lombok.AllArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.io.UnsupportedEncodingException;
import java.math.BigDecimal;
import java.net.URLEncoder;
import java.time.Clock;
import java.time.Instant;
import java.time.ZonedDateTime;
import java.util.List;
import java.util.Optional;

@Service
@AllArgsConstructor
public class UserService implements UserDetailsService {

    private static final Logger LOGGER = LoggerFactory.getLogger(UserService.class);

    // TODO: Externalize into templates
    private static final String REQUEST_TITLE = "Password reset request";
    private static final String REQUEST_MESSAGE = "Dear %s,\n\nA password reset has been triggered.\nPlease go to %s to reset your password.\nThis link will only be valid for 24 hours.\n\nRegards,\n\n%s";

    private static final String CONFIRMATION_TITLE = "Password reset confirmation";
    private static final String CONFIRMATION_MESSAGE = "Dear %s,\n\nYour password has been reset to:\n%s\n\nPlease login now and change it on the 'Settings' page.\n\nRegards,\n\n%s";

    private final UserRepository userRepository;

    private final PasswordResetTokenRepository passwordResetTokenRepository;

    private final MailService mailService;

    private final ConfigService configService;

    private final PasswordEncoder passwordEncoder;

    private final Clock clock;

    @Override
    public UserDetails loadUserByUsername(String email) throws UsernameNotFoundException {
        if (!email.isEmpty()) {
            LOGGER.debug("Querying user with email {} from database", email);
            return userRepository.findOneByEmailIgnoringCase(email)
                .orElseThrow(() -> new UsernameNotFoundException("User with email address " + email + " not found"));
        }
        throw new UsernameNotFoundException("No email address given for user query");
    }

    public Optional<User> getUser(String email) {
        return userRepository.findOneByEmailIgnoringCase(email);
    }

    public List<User> getAllUsers() {
        return userRepository.findAllByOrderByCreatedDateDesc();
    }

    public boolean registerUser(UserDto userDto) {
        User user = new User();
        user.setCreatedDate(Instant.now(clock));
        user.setLastModifiedDate(Instant.now(clock));
        user.setName(userDto.getName());
        user.setEmail(userDto.getEmail());
        user.setPassword(passwordEncoder.encode(userDto.getPassword()));
        // Defaults for new users
        user.setRole(User.ROLE_USER);
        user.setWager(BigDecimal.valueOf(0));
        try {
            userRepository.save(user);
            return true;
        } catch (Exception e) {
            LOGGER.error("Error creating new user: {}", e.getMessage());
        }
        return false;
    }

    public User updateUser(UserDataDto userDataDto, User user) {
        user.setName(userDataDto.getName());
        user.setPreferredLanguage(userDataDto.getPreferredLanguage());
        user.setLastModifiedDate(Instant.now(clock));
        userRepository.save(user);
        return user;
    }

    public boolean changePassword(PasswordDto passwordDto, User user) {
        if (passwordEncoder.matches(passwordDto.getOldPassword(), user.getPassword())) {
            changePassword(passwordDto.getNewPassword(), user);
            return true;
        }
        return false;
    }

    private void changePassword(String newPassword, User user) {
        user.setPassword(passwordEncoder.encode(newPassword));
        user.setLastModifiedDate(Instant.now(clock));
        userRepository.save(user);
    }

    public boolean requestPasswordReset(String email, String baseUrl) {

        LOGGER.info("Requesting password reset for email: {}", email);

        // Check for existing user
        Optional<User> user = userRepository.findOneByEmailIgnoringCase(email);
        if (!user.isPresent()) {
            LOGGER.error("Failed: user not found.");
            return false;
        }

        // Delete possibly existing tokens first
        if (user.get().getPasswordResetToken() != null) {
            passwordResetTokenRepository.delete(user.get().getPasswordResetToken());
        }

        // Create new reset token
        PasswordResetToken token = new PasswordResetToken(user.get());
        passwordResetTokenRepository.save(token);

        // Build the confirmation URL
        String urlTemplate = baseUrl + "/api/users/password/reset/%s/%s";
        String url;
        try {
            url = String.format(urlTemplate, URLEncoder.encode(token.getValue(), "UTF-8"), URLEncoder.encode(email, "UTF-8"));
        } catch (UnsupportedEncodingException e) {
            LOGGER.warn("Error building password reset confirmation URL: {}", e.getMessage());
            return false;
        }

        // Send URL to user
        Config config = configService.getConfig();
        if (mailService.send(email, config.getTitle() + ": " + REQUEST_TITLE, String.format(REQUEST_MESSAGE, user.get().getName(), url, config.getOwner()))) {
            LOGGER.info("Mail with password reset confirmation URL sent to user {}", email);
        }
        return true;
    }

    public void confirmPasswordReset(String email, String token) throws PasswordResetException {

        Optional<PasswordResetToken> passwordResetTokenOptional = passwordResetTokenRepository.findOneByValue(token);
        Optional<User> userOptional = userRepository.findOneByEmailIgnoringCase(email);

        // Check for correct params
        if (!passwordResetTokenOptional.isPresent()) {
            throw new PasswordResetException("Token not found.");
        }
        if (!userOptional.isPresent()) {
            throw new PasswordResetException("Email not found.");
        }
        PasswordResetToken passwordResetToken = passwordResetTokenOptional.get();
        User user = userOptional.get();

        // Check for correct user
        if (!passwordResetToken.getUser().equals(user)) {
            throw new PasswordResetException("Wrong token.");
        }

        // Check for token expiry
        if (passwordResetToken.getExpiry().isBefore(ZonedDateTime.now())) {
            passwordResetTokenRepository.delete(passwordResetToken);
            throw new PasswordResetException("Token expired.");
        }

        // Everything is OK, so we can delete the token
        passwordResetTokenRepository.delete(passwordResetToken);

        // Generate a new password and apply it
        LOGGER.info("Generating new password for user {}", email);
        String newPassword = PasswordGenerator.generate(16);
        changePassword(newPassword, user);

        // Send password to user
        Config config = configService.getConfig();
        if (mailService.send(email, config.getTitle() + ": " + CONFIRMATION_TITLE, String.format(CONFIRMATION_MESSAGE, user.getName(), newPassword, config.getOwner()))) {
            LOGGER.info("Mail with password sent to user {}", email);
        }
    }
}
