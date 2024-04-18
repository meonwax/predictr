package de.meonwax.predictr.controller;

import de.meonwax.predictr.entity.Config;
import de.meonwax.predictr.repository.ConfigRepository;
import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Get;

import java.util.Optional;

@Controller("/config")
public class ConfigController {

    private final ConfigRepository configRepository;

    ConfigController(ConfigRepository configRepository) {
        this.configRepository = configRepository;
    }

    @Get
    Optional<Config> index() {
        return configRepository.findAll()
            .stream()
            .findFirst();
    }
}
