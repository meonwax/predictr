package de.meonwax.predictr.security;

import de.meonwax.predictr.domain.RememberMeToken;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.repository.RememberMeTokenRepository;
import de.meonwax.predictr.repository.UserRepository;
import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.web.authentication.rememberme.PersistentRememberMeToken;
import org.springframework.security.web.authentication.rememberme.PersistentTokenRepository;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.util.Date;
import java.util.Optional;

@Component
@AllArgsConstructor
@Slf4j
public class CustomPersistentTokenRepository implements PersistentTokenRepository {

    private final RememberMeTokenRepository rememberMeTokenRepository;

    private final UserRepository userRepository;

    @Override
    public void createNewToken(PersistentRememberMeToken token) {
        RememberMeToken rememberMeToken = new RememberMeToken();
        Optional<User> user = userRepository.findOneByEmailIgnoringCase(token.getUsername());
        if (user.isPresent()) {
            rememberMeToken.setUser(user.get());
            rememberMeToken.setSeries(token.getSeries());
            rememberMeToken.setValue(token.getTokenValue());
            rememberMeToken.setDate(token.getDate());
            rememberMeTokenRepository.saveAndFlush(rememberMeToken);
            log.debug("Remember-me token for user {} created.", token.getUsername());
        } else {
            log.warn("Error creating remember-me token. User {} not found in database.", token.getUsername());
        }
    }

    @Override
    public void updateToken(String series, String tokenValue, Date lastUsed) {
        Optional<RememberMeToken> rememberMeToken = rememberMeTokenRepository.findById(series);
        if (rememberMeToken.isPresent()) {
            RememberMeToken token = rememberMeToken.get();
            token.setValue(tokenValue);
            token.setDate(lastUsed);
            rememberMeTokenRepository.saveAndFlush(token);
            log.debug("Remember-me token for series {} updated.", series);
        } else {
            log.warn("Error updating remember-me token. Token for series {} not found in database.", series);
        }
    }

    @Override
    public PersistentRememberMeToken getTokenForSeries(String seriesId) {
        return rememberMeTokenRepository.findById(seriesId)
            .map(token -> new PersistentRememberMeToken(
                token.getUser().getEmail(),
                token.getSeries(),
                token.getValue(),
                token.getDate()))
            .orElse(null);
    }

    @Override
    @Transactional
    public void removeUserTokens(String username) {
        Optional<User> user = userRepository.findOneByEmailIgnoringCase(username);
        if (user.isPresent()) {
            rememberMeTokenRepository.deleteByUser(user.get());
            log.debug("Remember-me token for user {} deleted.", username);
        } else {
            log.warn("Error deleting remember-me token. User {} not found in database.", username);
        }
    }
}
