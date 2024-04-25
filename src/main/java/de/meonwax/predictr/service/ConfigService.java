package de.meonwax.predictr.service;

import de.meonwax.predictr.domain.Config;
import de.meonwax.predictr.repository.ConfigRepository;
import lombok.AllArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@AllArgsConstructor
public class ConfigService {

    private final ConfigRepository configRepository;

    public Config getConfig() {
        return configRepository.getOne(1L);
    }
}
