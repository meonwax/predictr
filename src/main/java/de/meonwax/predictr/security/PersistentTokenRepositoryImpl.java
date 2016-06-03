package de.meonwax.predictr.security;

import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.Date;
import java.util.Set;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.web.authentication.rememberme.PersistentRememberMeToken;
import org.springframework.security.web.authentication.rememberme.PersistentTokenRepository;
import org.springframework.stereotype.Component;

import de.meonwax.predictr.domain.RememberMeToken;
import de.meonwax.predictr.repository.RememberMeTokenRepository;
import de.meonwax.predictr.repository.UserRepository;

@Component
public class PersistentTokenRepositoryImpl implements PersistentTokenRepository {

    private final Logger log = LoggerFactory.getLogger(PersistentTokenRepositoryImpl.class);

    @Autowired
    RememberMeTokenRepository rememberMeTokenRepository;

    @Autowired
    UserRepository userRepository;

    @Override
    public void createNewToken(PersistentRememberMeToken token) {
        log.info("Creating token for user " + token.getUsername());
        RememberMeToken rememberMeToken = new RememberMeToken();
        rememberMeToken.setUser(userRepository.findOneByEmailIgnoringCase(token.getUsername()));
        rememberMeToken.setSeries(token.getSeries());
        rememberMeToken.setValue(token.getTokenValue());
        rememberMeToken.setDate(ZonedDateTime.ofInstant(token.getDate().toInstant(), ZoneId.systemDefault()));
        rememberMeTokenRepository.save(rememberMeToken);
    }

    @Override
    public void updateToken(String seriesId, String tokenValue, Date lastUsed) {
        log.info("Updating token for seriesId: " + seriesId);
        RememberMeToken rememberMeToken = rememberMeTokenRepository.findOne(seriesId);
        rememberMeToken.setValue(tokenValue);
        rememberMeToken.setDate(ZonedDateTime.ofInstant(lastUsed.toInstant(), ZoneId.systemDefault()));
        rememberMeTokenRepository.save(rememberMeToken);
    }

    @Override
    public PersistentRememberMeToken getTokenForSeries(String seriesId) {
        log.info("Fetch token if any for seriesId: " + seriesId);
        RememberMeToken rememberMeToken = rememberMeTokenRepository.findOne(seriesId);
        if (rememberMeToken != null) {
            return new PersistentRememberMeToken(rememberMeToken.getUser().getEmail(), rememberMeToken.getSeries(), rememberMeToken.getValue(), Date.from(rememberMeToken.getDate().toInstant()));
        }
        log.info("Token not found.");
        return null;
    }

    @Override
    public void removeUserTokens(String username) {
        log.info("Removing token if any for user: " + username);
        Set<RememberMeToken> rememberMeTokens = rememberMeTokenRepository.findAllByUser(userRepository.findOneByEmailIgnoringCase(username));
        for (RememberMeToken rememberMeToken : rememberMeTokens) {
            rememberMeTokenRepository.delete(rememberMeToken);
            log.info("Token deleted for user " + username);
        }
    }
}
