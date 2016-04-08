package de.meonwax.web;

import java.util.List;

import javax.validation.Valid;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

import de.meonwax.dto.BetDto;
import de.meonwax.repository.BetRepository;

@RestController
@RequestMapping("api")
public class BetController {

    private final Logger log = LoggerFactory.getLogger(BetController.class);

    @Autowired
    private BetRepository betRepository;

    @RequestMapping(value = "/bets", method = RequestMethod.POST, produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Void> bet(@Valid @RequestBody List<BetDto> betDtos) {
        if (betDtos.isEmpty()) {
            return ResponseEntity.badRequest().build();
        }
        // TODO: Determine logged in user
        for (BetDto betDto : betDtos) {
            log.info(betDto.toString());
        }
        return ResponseEntity.noContent().build();
    }
}
