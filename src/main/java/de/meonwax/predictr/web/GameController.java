package de.meonwax.predictr.web;

import java.time.ZonedDateTime;
import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.MediaType;
import org.springframework.security.access.annotation.Secured;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

import de.meonwax.predictr.domain.Game;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.repository.GameRepository;

@RestController
@RequestMapping("api")
public class GameController {

    @Autowired
    private GameRepository gameRepository;

    @RequestMapping(value = "/games", method = RequestMethod.GET, produces = MediaType.APPLICATION_JSON_VALUE)
    @Secured(User.ROLE_ADMIN)
    public List<Game> getAll() {
        return gameRepository.findAll();
    }

    @RequestMapping(value = "/games/upcoming", method = RequestMethod.GET, produces = MediaType.APPLICATION_JSON_VALUE)
    public List<Game> getUpcoming() {
        return gameRepository.findByKickoffTimeAfterOrderByKickoffTime(new PageRequest(0, 5), ZonedDateTime.now());
    }

    @RequestMapping(value = "/games/running", method = RequestMethod.GET, produces = MediaType.APPLICATION_JSON_VALUE)
    public List<Game> getRunning() {
        return gameRepository.findByKickoffTimeBeforeAndScoreHomeIsNullAndScoreAwayIsNullOrderByKickoffTime(ZonedDateTime.now());
    }
}
