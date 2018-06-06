package de.meonwax.predictr.dto;

import de.meonwax.predictr.domain.Config;
import de.meonwax.predictr.service.ConfigService;
import de.meonwax.predictr.settings.Settings;
import lombok.AllArgsConstructor;
import org.springframework.stereotype.Component;

import java.time.ZonedDateTime;
import java.util.List;

@Component
@AllArgsConstructor
public class ServerInfo {

    private final Settings settings;

    private final ConfigService configService;

    public ZonedDateTime getTime() {
        return ZonedDateTime.now();
    }

    public String getVersion() {
        return settings.getVersion();
    }

    public String getTitle() {
        return configService.getConfig().getTitle();
    }

    public String getOwner() {
        return configService.getConfig().getOwner();
    }

    public String getAdminEmail() {
        return configService.getConfig().getAdminEmail();
    }

    public Boolean getShowImportantMessage() {
        return configService.getConfig().getShowImportantMessage();
    }

    public List<String> getPagesBlacklist() {
        return settings.getPagesBlacklist();
    }

    public Integer getPointsResult() {
        return configService.getConfig().getPointsResult();
    }

    public Integer getPointsTendencySpread() {
        return configService.getConfig().getPointsTendencySpread();
    }

    public Integer getPointsTendency() {
        return configService.getConfig().getPointsTendency();
    }

    public RulesDto getRules() {
        Config config = configService.getConfig();
        return new RulesDto(config.getRulesEn(), config.getRulesDe());
    }
}
