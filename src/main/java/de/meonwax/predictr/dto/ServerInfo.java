package de.meonwax.predictr.dto;

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
    private Integer pointsResult;

    @Value("${predictr.points.tendency}")
    private Integer pointsTendency;

    @Value("${predictr.points.tendencySpread}")
    private Integer pointsTendencySpread;

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

    public Integer getPointsResult() {
        return pointsResult;
    }

    public Integer getPointsTendency() {
        return pointsTendency;
    }

    public Integer getPointsTendencySpread() {
        return pointsTendencySpread;
    }
}
