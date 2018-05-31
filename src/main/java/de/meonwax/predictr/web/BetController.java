package de.meonwax.predictr.web;

import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.dto.BetDto;
import de.meonwax.predictr.service.BetService;
import lombok.AllArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.List;

@RestController
@RequestMapping("api")
@AllArgsConstructor
public class BetController {

    private final BetService betService;

    @RequestMapping(value = "/bets", method = RequestMethod.POST, produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Void> bet(@Valid @RequestBody List<BetDto> betDtos, @AuthenticationPrincipal User user) {
        if (betDtos.isEmpty()) {
            return ResponseEntity.badRequest().build();
        }
        betService.update(user, betDtos);
        return ResponseEntity.noContent().build();
    }

    /**
     * Retrieve the bets of other users for an already started game
     */
    @RequestMapping(value = "/bets/{gameId}", method = RequestMethod.GET, produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<List<BetDto>> getOther(@PathVariable Long gameId, @AuthenticationPrincipal User user) {
        return betService.getOther(user, gameId)
            .map(bets -> new ResponseEntity<>(bets, HttpStatus.OK))
            .orElse(new ResponseEntity<>(HttpStatus.LOCKED));
    }
}
