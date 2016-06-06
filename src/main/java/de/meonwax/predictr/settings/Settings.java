package de.meonwax.predictr.settings;

import java.util.List;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.NestedConfigurationProperty;
import org.springframework.stereotype.Component;

@Component
@ConfigurationProperties(prefix = "predictr")
public class Settings {

    private String title;

    private String owner;

    private String version;

    private String adminEmail;

    private Boolean registrationEnabled;

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

    public String getAdminEmail() {
        return adminEmail;
    }

    public void setAdminEmail(String adminEmail) {
        this.adminEmail = adminEmail;
    }

    public Boolean getRegistrationEnabled() {
        return registrationEnabled;
    }

    public void setRegistrationEnabled(Boolean registrationEnabled) {
        this.registrationEnabled = registrationEnabled;
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