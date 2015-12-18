package de.meonwax.web;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.env.Environment;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

import de.meonwax.dto.ServerInfo;

@RestController
@RequestMapping("api")
public class InfoController {

    private final Logger log = LoggerFactory.getLogger(InfoController.class);

    @Autowired
    private Environment env;

    @RequestMapping(value = "/info", method = RequestMethod.GET, produces = MediaType.APPLICATION_JSON_VALUE)
    public ServerInfo get() {
        return new ServerInfo(env.getProperty("predictr.version", "unknown"), env.getProperty("predictr.title", "Predictr"));
    }
}
