package de.meonwax.predictr.web;

import de.meonwax.predictr.domain.Team;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.repository.TeamRepository;
import lombok.AllArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.security.access.annotation.Secured;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("api")
@AllArgsConstructor
public class TeamController {

    private final TeamRepository teamRepository;

    @RequestMapping(value = "/teams", method = RequestMethod.GET, produces = MediaType.APPLICATION_JSON_VALUE)
    @Secured(User.ROLE_ADMIN)
    public List<Team> getAll() {
        return teamRepository.findAllByOrderById();
    }
}
