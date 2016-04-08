package de.meonwax.web;

import java.time.ZonedDateTime;
import java.util.List;

import javax.validation.Valid;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import de.meonwax.domain.Shout;
import de.meonwax.dto.ShoutDto;
import de.meonwax.repository.ShoutRepository;
import de.meonwax.repository.UserRepository;

@RestController
@RequestMapping("api")
public class ShoutController {

    @Autowired
    private ShoutRepository shoutRepository;

    @Autowired
    private UserRepository userRepository;

    @RequestMapping(value = "/shouts", method = RequestMethod.GET, produces = MediaType.APPLICATION_JSON_VALUE)
    public List<Shout> getAll(@RequestParam(value = "limit", required = false, defaultValue = "100") Integer limit) {
        return shoutRepository.findAllByOrderByDateDesc(new PageRequest(0, limit)).getContent();
    }

    @RequestMapping(value = "/shouts", method = RequestMethod.POST, produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Void> create(@Valid @RequestBody ShoutDto shoutDto) {
        // TODO: Determine logged in user
        Shout shout = new Shout(ZonedDateTime.now(), shoutDto.getMessage(), userRepository.findOneByEmailIgnoringCase("sid@example.com"));
        shoutRepository.save(shout);
        return ResponseEntity.status(HttpStatus.CREATED).build();
    }
}
