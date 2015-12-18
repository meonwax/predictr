package de.meonwax.web;

import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

import de.meonwax.domain.Shout;
import de.meonwax.repository.ShoutRepository;

@RestController
@RequestMapping("api")
public class ShoutController {

    private final Logger log = LoggerFactory.getLogger(ShoutController.class);

    @Autowired
    private ShoutRepository shoutRepository;

    @RequestMapping(value = "/shouts", method = RequestMethod.GET, produces = MediaType.APPLICATION_JSON_VALUE)
    public List<Shout> getAll() {
        return shoutRepository.findAll();
    }
}
