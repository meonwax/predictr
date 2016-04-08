package de.meonwax.web;

import java.math.BigDecimal;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

import de.meonwax.domain.User;
import de.meonwax.repository.UserRepository;

@RestController
@RequestMapping("api")
public class UserController {

    private final Logger log = LoggerFactory.getLogger(UserController.class);

    @Autowired
    private UserRepository userRepository;

    @RequestMapping(value = "/account", method = RequestMethod.GET, produces = MediaType.APPLICATION_JSON_VALUE)
    public User getAccount() {
        // TODO: Determine logged in user
        return userRepository.findOneByEmailIgnoringCase("sid@example.com");
    }

    @RequestMapping(value = "/users/jackpot", method = RequestMethod.GET, produces = MediaType.APPLICATION_JSON_VALUE)
    public BigDecimal getJackpot() {
        return userRepository.getJackpot();
    }
}
