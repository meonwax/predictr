package de.meonwax.dto;

import java.io.Serializable;
import java.time.ZonedDateTime;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class ServerInfo implements Serializable {

    private static final long serialVersionUID = 1L;

    @Value("${predictr.version}")
    private String version;

    @Value("${predictr.title}")
    private String title;

    @Value("${predictr.owner}")
    private String owner;

    @Value("${predictr.adminEmail}")
    private String adminEmail;

    @Value("${predictr.points.result}")
    private int pointsResult;

    @Value("${predictr.points.tendency}")
    private int pointsTendency;

    @Value("${predictr.points.tendencySpread}")
    private int pointsTendencySpread;

    public ServerInfo() {
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

    public String getOwner() {
        return owner;
    }

    public String getAdminEmail() {
        return adminEmail;
    }

    public int getPointsResult() {
        return pointsResult;
    }

    public int getPointsTendency() {
        return pointsTendency;
    }

    public int getPointsTendencySpread() {
        return pointsTendencySpread;
    }
}
