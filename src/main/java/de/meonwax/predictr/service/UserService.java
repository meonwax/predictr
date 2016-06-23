package de.meonwax.predictr.service;

import java.io.UnsupportedEncodingException;
import java.math.BigDecimal;
import java.net.URLEncoder;
import java.time.ZonedDateTime;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import de.meonwax.predictr.domain.PasswordResetToken;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.dto.PasswordDto;
import de.meonwax.predictr.dto.UserDataDto;
import de.meonwax.predictr.dto.UserDto;
import de.meonwax.predictr.exception.PasswordResetException;
import de.meonwax.predictr.repository.PasswordResetTokenRepository;
import de.meonwax.predictr.repository.UserRepository;
import de.meonwax.predictr.settings.Settings;
import de.meonwax.predictr.util.PasswortGenerator;
import de.meonwax.predictr.util.Utils;

@Service
public class UserService implements UserDetailsService {

    private final Logger log = LoggerFactory.getLogger(UserService.class);

    // TODO: Externalize into templates
    private final static String REQUEST_TITLE = "Password reset request";
    private final static String REQUEST_MESSAGE = "Dear %s,\n\nA password reset has been triggered.\nPlease go to %s to reset your password.\nThis link will only be valid for 24 hours.\n\nRegards,\n\n%s";

    private final static String CONFIRMATION_TITLE = "Password reset confirmation";
    private final static String CONFIRMATION_MESSAGE = "Dear %s,\n\nYour password has been reset to:\n%s\n\nPlease login now and change it on the 'Settings' page.\n\nRegards,\n\n%s";

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private PasswordResetTokenRepository passwordResetTokenRepository;

    @Autowired
    private MailService mailService;

    @Autowired
    private Settings settings;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @Override
    public UserDetails loadUserByUsername(String email) throws UsernameNotFoundException {
        if (email.length() > 0) {
            log.debug("Querying user with email " + email + " from database");
            User user = userRepository.findOneByEmailIgnoringCase(email);
            if (user != null) {
                return user;
            }
            throw new UsernameNotFoundException("User with email address " + email + " not found");
        }
        throw new UsernameNotFoundException("No email address given for user query");
    }

    public User getUser(String email) {
        return userRepository.findOneByEmailIgnoringCase(email);
    }

    public List<User> getAllUsers() {
        return userRepository.findAllByOrderByCreatedDateDesc();
    }

    public boolean registerUser(UserDto userDto) {
        User user = new User();
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
            log.error("Error creating new user: " + e.getMessage());
        }
        return false;
    }

    public User updateUser(UserDataDto userDataDto, User user) {
        user.setName(userDataDto.getName());
        user.setPreferredLanguage(userDataDto.getPreferredLanguage());
        user.setLastModifiedDate(ZonedDateTime.now());
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
        user.setLastModifiedDate(ZonedDateTime.now());
        userRepository.save(user);
    }

    public boolean requestPasswordReset(String email, String baseUrl) {

        log.info("Requesting password reset for email: " + email);

        // Check for existing user
        User user = userRepository.findOneByEmailIgnoringCase(email);
        if (user == null) {
            log.error("Failed: user not found.");
            return false;
        }

        // Delete possibly existing tokens first
        if (user.getPasswordResetToken() != null) {
            passwordResetTokenRepository.delete(user.getPasswordResetToken());
        }

        // Create new reset token
        PasswordResetToken token = new PasswordResetToken(user);
        passwordResetTokenRepository.save(token);

        // Build the confirm URL
        String urlTemplate = baseUrl + "/api/users/password/reset/%s/%s";
        String url;
        try {
            url = String.format(urlTemplate, URLEncoder.encode(token.getValue(), "UTF-8"), URLEncoder.encode(email, "UTF-8"));
        } catch (UnsupportedEncodingException e) {
            e.printStackTrace();
            return false;
        }

        // Send URL to user
        if (mailService.send(email, settings.getTitle() + ": " + REQUEST_TITLE, String.format(REQUEST_MESSAGE, user.getName(), url, settings.getOwner()))) {
            log.info("Mail sent.");
        }
        return true;
    }

    public void confirmPasswordReset(String email, String token) throws PasswordResetException {

        PasswordResetToken passwordResetToken = passwordResetTokenRepository.findOneByValue(token);
        User user = userRepository.findOneByEmailIgnoringCase(email);

        // Check for correct params
        if (!Utils.allNotNull(passwordResetToken, user)) {
            throw new PasswordResetException("Email or token not found.");
        }

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
        log.info("Generating new password for user " + email);
        String newPassword = PasswortGenerator.generate(16);
        changePassword(newPassword, user);

        // Send password to user
        if (mailService.send(email, settings.getTitle() + ": " + CONFIRMATION_TITLE, String.format(CONFIRMATION_MESSAGE, user.getName(), newPassword, settings.getOwner()))) {
            log.info("Mail sent.");
        }
    }
}
