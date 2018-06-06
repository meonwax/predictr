package de.meonwax.predictr.settings;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
@ConfigurationProperties(prefix = "predictr")
@Data
public class Settings {

    private String version;

    private String rememberMeKey;

    private List<String> pagesBlacklist;
}
