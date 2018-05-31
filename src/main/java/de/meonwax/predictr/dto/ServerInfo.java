package de.meonwax.predictr.dto;

import de.meonwax.predictr.settings.Points;
import de.meonwax.predictr.settings.Settings;
import lombok.AllArgsConstructor;
import org.springframework.stereotype.Component;

import java.time.ZonedDateTime;
import java.util.List;

@Component
@AllArgsConstructor
public class ServerInfo {

    private final Settings settings;

    public ZonedDateTime getTime() {
        return ZonedDateTime.now();
    }

    public String getVersion() {
        return settings.getVersion();
    }

    public String getTitle() {
        return settings.getTitle();
    }

    public String getOwner() {
        return settings.getOwner();
    }

    public String getAdminEmail() {
        return settings.getAdminEmail();
    }

    public Boolean getShowImportantMessage() {
        return settings.getShowImportantMessage();
    }

    public List<String> getPagesBlacklist() {
        return settings.getPagesBlacklist();
    }

    public Points getPoints() {
        return settings.getPoints();
    }
}
