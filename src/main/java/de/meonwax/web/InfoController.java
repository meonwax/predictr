package de.meonwax.web;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

import de.meonwax.dto.ServerInfo;

@RestController
@RequestMapping("api")
public class InfoController {

    @Autowired
    private ServerInfo serverInfo;

    @RequestMapping(value = "/info", method = RequestMethod.GET, produces = MediaType.APPLICATION_JSON_VALUE)
    public ServerInfo get() {
        return serverInfo;
    }
}
