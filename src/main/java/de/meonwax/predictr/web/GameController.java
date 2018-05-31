package de.meonwax.predictr.web;

import de.meonwax.predictr.domain.Game;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.dto.GameDto;
import de.meonwax.predictr.service.GameService;
import lombok.AllArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.annotation.Secured;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

import javax.validation.Valid;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("api")
@AllArgsConstructor
public class GameController {

    private final GameService gameService;

    @RequestMapping(value = "/games", method = RequestMethod.GET, produces = MediaType.APPLICATION_JSON_VALUE)
    @Secured(User.ROLE_ADMIN)
    public List<Game> getAll() {
        return gameService.getAll();
    }

    @RequestMapping(value = "/games", method = RequestMethod.POST, produces = MediaType.APPLICATION_JSON_VALUE)
    @Secured(User.ROLE_ADMIN)
    public ResponseEntity<Void> save(@Valid @RequestBody List<GameDto> gameDtos) {
        if (gameDtos.isEmpty()) {
            return ResponseEntity.badRequest().build();
        }
        gameService.update(gameDtos);
        return ResponseEntity.noContent().build();
    }

    @RequestMapping(value = "/games/upcoming", method = RequestMethod.GET, produces = MediaType.APPLICATION_JSON_VALUE)
    public List<Game> getUpcoming() {
        return gameService.getUpcoming();
    }

    @RequestMapping(value = "/games/running", method = RequestMethod.GET, produces = MediaType.APPLICATION_JSON_VALUE)
    public List<Game> getRunning() {
        return gameService.getRunning();
    }

    @RequestMapping(value = "/games/progress", method = RequestMethod.GET, produces = MediaType.APPLICATION_JSON_VALUE)
    public Map<String, Long> getProgress() {
        return gameService.getProgress();
    }
}
