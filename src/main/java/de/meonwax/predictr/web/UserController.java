package de.meonwax.predictr.web;

import de.meonwax.predictr.domain.Config;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.dto.PasswordDto;
import de.meonwax.predictr.dto.UserDataDto;
import de.meonwax.predictr.dto.UserDto;
import de.meonwax.predictr.exception.PasswordResetException;
import de.meonwax.predictr.service.ConfigService;
import de.meonwax.predictr.service.MailService;
import de.meonwax.predictr.service.UserService;
import de.meonwax.predictr.util.Utils;
import lombok.AllArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.annotation.Secured;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import javax.servlet.http.HttpServletRequest;
import javax.validation.Valid;
import javax.validation.constraints.Email;
import java.util.List;

@RestController
@RequestMapping("api")
@AllArgsConstructor
public class UserController {

    private static final Logger LOGGER = LoggerFactory.getLogger(UserController.class);

    private final UserService userService;

    private final MailService mailService;

    private final ConfigService configService;

    @RequestMapping(value = "/users/register", method = RequestMethod.POST, produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Void> register(@Valid @RequestBody UserDto userDto) {
        if (userService.registerUser(userDto)) {
            String msg = "User registered: " + userDto.toString();
            LOGGER.info(msg);
            if (mailService.isEnabled()) {
                Config config = configService.getConfig();
                mailService.send(config.getAdminEmail(), config.getTitle() + ": New user registered", msg);
            }
            return ResponseEntity.status(HttpStatus.CREATED).build();
        }
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
    }

    @RequestMapping(value = "/users", method = RequestMethod.GET, produces = MediaType.APPLICATION_JSON_VALUE)
    @Secured(User.ROLE_ADMIN)
    public ResponseEntity<List<User>> getAllUsers() {
        return ResponseEntity.ok().body(userService.getAllUsers());
    }

    @RequestMapping(value = "/users/account", method = RequestMethod.GET, produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<User> getAccount(@AuthenticationPrincipal User user) {
        return ResponseEntity.ok(userService.getUser(user.getEmail()));
    }

    @RequestMapping(value = "/users/account", method = RequestMethod.POST, produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<User> updateAccount(@Valid @RequestBody UserDataDto userDataDto, @AuthenticationPrincipal User user) {
        User updatedUser = userService.updateUser(userDataDto, user);
        return ResponseEntity.ok(updatedUser);
    }

    @RequestMapping(value = "/users/password/change", method = RequestMethod.POST, produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Void> changePassword(@Valid @RequestBody PasswordDto passwordDto, @AuthenticationPrincipal User user) {
        if (userService.changePassword(passwordDto, user)) {
            return ResponseEntity.ok().build();
        }
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
    }

    @RequestMapping(value = "/users/password/resetRequest", method = RequestMethod.POST, produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Void> requestPasswordReset(@Email @RequestBody String email, HttpServletRequest request) {
        String baseUrl = Utils.getBaseUrl(request);
        if (userService.requestPasswordReset(email, baseUrl)) {
            return ResponseEntity.ok().build();
        }
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).build();
    }

    @RequestMapping(value = "/users/password/reset/{token}/{email:.+}", method = RequestMethod.GET, produces = MediaType.TEXT_HTML_VALUE)
    public ResponseEntity<String> confirmPasswordReset(@PathVariable String token, @PathVariable String email) {
        try {
            userService.confirmPasswordReset(email, token);
            return ResponseEntity.status(HttpStatus.FOUND).header(HttpHeaders.LOCATION, "/").body("");
        } catch (PasswordResetException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body("<h2>Error</h2><h3>" + e.getMessage() + "</h3>");
        }
    }
}
