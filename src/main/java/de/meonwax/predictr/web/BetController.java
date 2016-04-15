package de.meonwax.predictr.web;

import java.util.List;

import javax.validation.Valid;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.dto.BetDto;
import de.meonwax.predictr.service.BetService;

@RestController
@RequestMapping("api")
public class BetController {

    @Autowired
    private BetService betService;

    @RequestMapping(value = "/bets", method = RequestMethod.POST, produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Void> bet(@Valid @RequestBody List<BetDto> betDtos, @AuthenticationPrincipal User user) {
        if (betDtos.isEmpty()) {
            return ResponseEntity.badRequest().build();
        }
        betService.update(user, betDtos);
        return ResponseEntity.noContent().build();
    }
}
