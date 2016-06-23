package de.meonwax.predictr.web;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.security.access.annotation.Secured;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

import de.meonwax.predictr.domain.Team;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.repository.TeamRepository;

@RestController
@RequestMapping("api")
public class TeamController {

    @Autowired
    private TeamRepository teamRepository;

    @RequestMapping(value = "/teams", method = RequestMethod.GET, produces = MediaType.APPLICATION_JSON_VALUE)
    @Secured(User.ROLE_ADMIN)
    public List<Team> getAll() {
        return teamRepository.findAll();
    }
}
