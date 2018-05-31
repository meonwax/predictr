package de.meonwax.predictr.security;

import de.meonwax.predictr.domain.RememberMeToken;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.repository.RememberMeTokenRepository;
import de.meonwax.predictr.repository.UserRepository;
import de.meonwax.predictr.settings.Settings;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DataAccessException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.web.authentication.rememberme.AbstractRememberMeServices;
import org.springframework.security.web.authentication.rememberme.CookieTheftException;
import org.springframework.security.web.authentication.rememberme.InvalidCookieException;
import org.springframework.security.web.authentication.rememberme.RememberMeAuthenticationException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.security.SecureRandom;
import java.time.ZonedDateTime;
import java.util.Arrays;
import java.util.Base64;
import java.util.Optional;

/**
 * Custom implementation of Spring Security's RememberMeServices inspired by the implementation at https://github.com/jhipster
 */
@Service
public class CustomPersistentRememberMeServices extends AbstractRememberMeServices {

    // Token is valid for two weeks
    private static final int TOKEN_VALIDITY_DAYS = 14;
    private static final int TOKEN_VALIDITY_SECONDS = 60 * 60 * 24 * TOKEN_VALIDITY_DAYS;

    private static final int DEFAULT_SERIES_LENGTH = 16;
    private static final int DEFAULT_TOKEN_LENGTH = 16;

    private static final Logger LOGGER = LoggerFactory.getLogger(CustomPersistentRememberMeServices.class);

    private final RememberMeTokenRepository rememberMeTokenRepository;

    private final UserRepository userRepository;

    private SecureRandom random;

    public CustomPersistentRememberMeServices(Settings settings, UserDetailsService userDetailsService, RememberMeTokenRepository rememberMeTokenRepository, UserRepository userRepository) {
        super(settings.getRememberMeKey(), userDetailsService);
        this.rememberMeTokenRepository = rememberMeTokenRepository;
        this.userRepository = userRepository;
    }

    @Override
    @Transactional
    protected UserDetails processAutoLoginCookie(String[] cookieTokens, HttpServletRequest request, HttpServletResponse response) throws RememberMeAuthenticationException, UsernameNotFoundException {

        RememberMeToken token = getRememberMeToken(cookieTokens);
        String email = token.getUser().getEmail();

        // Token also matches, so login is valid. Update the token date, keeping the *same* series number.
        LOGGER.debug("Refreshing persistent login token for user '{}', series '{}'", email, token.getSeries());
        token.setDate(ZonedDateTime.now());

        // Do not actually update the token value to circumvent a possible CookieTheftException when requests from client come in to quickly.
        // See here: https://github.com/spring-projects/spring-security/issues/3079
        // And here: http://stackoverflow.com/a/20055928

        //token.setValue(generateTokenData());

        try {
            rememberMeTokenRepository.saveAndFlush(token);
            addCookie(token, request, response);
        } catch (DataAccessException e) {
            LOGGER.error("Failed to update token: ", e);
            throw new RememberMeAuthenticationException("Autologin failed due to data access problem", e);
        }
        return getUserDetailsService().loadUserByUsername(email);
    }

    @Override
    protected void onLoginSuccess(HttpServletRequest request, HttpServletResponse response, Authentication successfulAuthentication) {
        String email = successfulAuthentication.getName();
        LOGGER.debug("Creating new persistent login for user {}", email);
        User user = userRepository.findOneByEmailIgnoringCase(email);
        RememberMeToken token;
        if (user != null) {
            token = new RememberMeToken();
            token.setSeries(generateSeriesData());
            token.setUser(user);
            token.setValue(generateTokenData());
            token.setDate(ZonedDateTime.now());
        } else {
            throw new UsernameNotFoundException("User " + email + " was not found in the database");
        }
        try {
            rememberMeTokenRepository.saveAndFlush(token);
            addCookie(token, request, response);
        } catch (DataAccessException e) {
            LOGGER.error("Failed to save persistent token ", e);
        }
    }

    /**
     * When logout occurs, only invalidate the current token and not all user sessions.
     * The standard Spring Security implementations are too basic: they invalidate all tokens for the
     * current user, so when he logs out from one browser, all his other sessions are destroyed.
     */
    @Override
    @Transactional
    public void logout(HttpServletRequest request, HttpServletResponse response, Authentication authentication) {
        String rememberMeCookie = extractRememberMeCookie(request);
        if (rememberMeCookie != null && rememberMeCookie.length() != 0) {
            try {
                String[] cookieTokens = decodeCookie(rememberMeCookie);
                RememberMeToken token = getRememberMeToken(cookieTokens);
                rememberMeTokenRepository.delete(token);
            } catch (InvalidCookieException e) {
                LOGGER.info("Invalid cookie, no persistent token could be deleted");
            } catch (RememberMeAuthenticationException e) {
                LOGGER.debug("No persistent token found, so no token could be deleted");
            }
        }
        super.logout(request, response, authentication);
    }

    /**
     * Validate the token and return it.
     */
    private RememberMeToken getRememberMeToken(String[] cookieTokens) {
        if (cookieTokens.length != 2) {
            throw new InvalidCookieException("Cookie token did not contain " + 2 + " tokens, but contained '" + Arrays.asList(cookieTokens) + "'");
        }
        String presentedSeries = cookieTokens[0];
        String presentedToken = cookieTokens[1];
        Optional<RememberMeToken> token = rememberMeTokenRepository.findById(presentedSeries);

        if (!token.isPresent()) {
            // No series match, so we can't authenticate using this cookie
            throw new RememberMeAuthenticationException("No persistent token found for series id: " + presentedSeries);
        }

        // We have a match for this user/series combination
        LOGGER.debug("presentedToken={} / tokenValue={}", presentedToken, token.get().getValue());
        if (!presentedToken.equals(token.get().getValue())) {
            // Token doesn't match series value. Delete this session and throw an exception.
            rememberMeTokenRepository.delete(token.get());
            throw new CookieTheftException("Invalid remember-me token (Series/token) mismatch. Implies previous cookie theft attack.");
        }

        if (token.get().getDate().plusDays(TOKEN_VALIDITY_DAYS).isBefore(ZonedDateTime.now())) {
            rememberMeTokenRepository.delete(token.get());
            throw new RememberMeAuthenticationException("Remember-me login has expired");
        }

        LOGGER.info("User " + token.get().getUser().getEmail() + " logged in using RememberMeToken");

        return token.get();
    }

    private String generateTokenData() {
        byte[] newToken = new byte[DEFAULT_TOKEN_LENGTH];
        random.nextBytes(newToken);
        return Base64.getEncoder().encodeToString(newToken);
    }

    private String generateSeriesData() {
        byte[] newSeries = new byte[DEFAULT_SERIES_LENGTH];
        random.nextBytes(newSeries);
        return Base64.getEncoder().encodeToString(newSeries);
    }

    private void addCookie(RememberMeToken token, HttpServletRequest request, HttpServletResponse response) {
        setCookie(new String[]{token.getSeries(), token.getValue()}, TOKEN_VALIDITY_SECONDS, request, response);
    }
}
