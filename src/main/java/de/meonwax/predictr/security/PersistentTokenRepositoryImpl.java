package de.meonwax.predictr.security;

import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.Date;

import javax.transaction.Transactional;

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
@Transactional
public class PersistentTokenRepositoryImpl implements PersistentTokenRepository {

    private final Logger log = LoggerFactory.getLogger(PersistentTokenRepositoryImpl.class);

    @Autowired
    private RememberMeTokenRepository rememberMeTokenRepository;

    @Autowired
    private UserRepository userRepository;

    @Override
    public void createNewToken(PersistentRememberMeToken token) {
        log.debug("Creating new RememberMeToken for user " + token.getUsername());
        RememberMeToken rememberMeToken = new RememberMeToken();
        rememberMeToken.setUser(userRepository.findOneByEmailIgnoringCase(token.getUsername()));
        rememberMeToken.setSeries(token.getSeries());
        rememberMeToken.setValue(token.getTokenValue());
        rememberMeToken.setDate(ZonedDateTime.ofInstant(token.getDate().toInstant(), ZoneId.systemDefault()));
        rememberMeTokenRepository.save(rememberMeToken);
    }

    @Override
    public void updateToken(String seriesId, String tokenValue, Date lastUsed) {
        log.debug("Updating RememberMeToken for series " + seriesId);
        RememberMeToken rememberMeToken = rememberMeTokenRepository.findOne(seriesId);
        rememberMeToken.setValue(tokenValue);
        rememberMeToken.setDate(ZonedDateTime.ofInstant(lastUsed.toInstant(), ZoneId.systemDefault()));
        rememberMeTokenRepository.save(rememberMeToken);
    }

    @Override
    public PersistentRememberMeToken getTokenForSeries(String seriesId) {
        log.debug("Try to find RememberMeToken for series " + seriesId);
        RememberMeToken rememberMeToken = rememberMeTokenRepository.findOne(seriesId);
        if (rememberMeToken != null) {
            log.info("User " + rememberMeToken.getUser().getEmail() + " logged in using RememberMeToken");
            return new PersistentRememberMeToken(rememberMeToken.getUser().getEmail(), rememberMeToken.getSeries(), rememberMeToken.getValue(), Date.from(rememberMeToken.getDate().toInstant()));
        }
        return null;
    }

    @Override
    public void removeUserTokens(String email) {
        log.debug("Deleting all RememberMeTokens for user " + email);
        Long count = rememberMeTokenRepository.deleteByUser(userRepository.findOneByEmailIgnoringCase(email));
        log.debug(count + " token(s) deleted");
    }
}
