package de.meonwax.dto;

import java.io.Serializable;
import java.time.ZonedDateTime;

public class ServerInfo implements Serializable {

    private static final long serialVersionUID = 1L;

    private String version;

    private String title;

    public ServerInfo(String version, String title) {
        this.version = version;
        this.title = title;
    }

    public ZonedDateTime getTime() {
        return ZonedDateTime.now();
    }

    public String getVersion() {
        return version;
    }

    public String getTitle() {
        return title;
    }
}
