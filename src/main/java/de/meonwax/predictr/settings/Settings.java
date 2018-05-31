package de.meonwax.predictr.settings;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.NestedConfigurationProperty;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
@ConfigurationProperties(prefix = "predictr")
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

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getOwner() {
        return owner;
    }

    public void setOwner(String owner) {
        this.owner = owner;
    }

    public String getVersion() {
        return version;
    }

    public void setVersion(String version) {
        this.version = version;
    }

    public String getRememberMeKey() {
        return rememberMeKey;
    }

    public void setRememberMeKey(String rememberMeKey) {
        this.rememberMeKey = rememberMeKey;
    }

    public String getAdminEmail() {
        return adminEmail;
    }

    public void setAdminEmail(String adminEmail) {
        this.adminEmail = adminEmail;
    }

    public Boolean getShowImportantMessage() {
        return showImportantMessage;
    }

    public void setShowImportantMessage(Boolean showImportantMessage) {
        this.showImportantMessage = showImportantMessage;
    }

    public List<String> getPagesBlacklist() {
        return pagesBlacklist;
    }

    public void setPagesBlacklist(List<String> pagesBlacklist) {
        this.pagesBlacklist = pagesBlacklist;
    }

    public Points getPoints() {
        return points;
    }

    public void setPoints(Points points) {
        this.points = points;
    }
}
