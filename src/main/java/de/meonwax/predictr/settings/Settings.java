package de.meonwax.predictr.settings;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.NestedConfigurationProperty;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
@ConfigurationProperties(prefix = "predictr")
@Data
public class Settings {

    private String title;

    private String owner;

    private String version;

    private String rememberMeKey;

    private String adminEmail;

    private Boolean showImportantMessage;

    private List<String> pagesBlacklist;

    @NestedConfigurationProperty
    private Points points;
}
