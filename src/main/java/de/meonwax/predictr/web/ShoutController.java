package de.meonwax.predictr.web;

import de.meonwax.predictr.domain.Shout;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.dto.ShoutDto;
import de.meonwax.predictr.repository.ShoutRepository;
import lombok.AllArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.time.Clock;
import java.time.Instant;
import java.util.List;

@RestController
@RequestMapping("api")
@AllArgsConstructor
public class ShoutController {

    private final ShoutRepository shoutRepository;

    private final Clock clock;

    @RequestMapping(value = "/shouts", method = RequestMethod.GET, produces = MediaType.APPLICATION_JSON_VALUE)
    public List<Shout> getAll(@RequestParam(value = "limit", required = false, defaultValue = "100") Integer limit) {
        return shoutRepository.findAllByOrderByDateDesc(PageRequest.of(0, limit)).getContent();
    }

    @RequestMapping(value = "/shouts", method = RequestMethod.POST, produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Void> create(@Valid @RequestBody ShoutDto shoutDto, @AuthenticationPrincipal User user) {
        Shout shout = new Shout(Instant.now(clock), shoutDto.getMessage(), user);
        shoutRepository.save(shout);
        return ResponseEntity.status(HttpStatus.CREATED).build();
    }
}
