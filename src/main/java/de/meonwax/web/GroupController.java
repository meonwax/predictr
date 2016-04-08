package de.meonwax.web;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

import de.meonwax.domain.Group;
import de.meonwax.repository.GroupRepository;

@RestController
@RequestMapping("api")
public class GroupController {

    @Autowired
    private GroupRepository groupRepository;

    @RequestMapping(value = "/groups", method = RequestMethod.GET, produces = MediaType.APPLICATION_JSON_VALUE)
    public List<Group> getAll() {
        return groupRepository.findAll();
    }
}
