package de.meonwax.predictr.dto;

import java.io.Serializable;
import java.time.ZonedDateTime;
import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import de.meonwax.predictr.settings.Points;
import de.meonwax.predictr.settings.Settings;

@Component
public class ServerInfo implements Serializable {

    private static final long serialVersionUID = 1L;

    @Autowired
    private Settings settings;

    public ServerInfo() {
    }

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

    public List<String> getPagesBlacklist() {
        return settings.getBlacklist();
    }

    public Points getPoints() {
        return settings.getPoints();
    }
}
