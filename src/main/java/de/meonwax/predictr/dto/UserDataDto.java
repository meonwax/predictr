package de.meonwax.predictr.dto;

import javax.validation.constraints.NotNull;
import javax.validation.constraints.Size;

import de.meonwax.predictr.util.Utils;

public class UserDataDto {

    @NotNull
    @Size(max = 255)
    private String name;

    @NotNull
    @Size(min = 2, max = 2)
    private String preferredLanguage;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getPreferredLanguage() {
        return preferredLanguage;
    }

    public void setPreferredLanguage(String preferredLanguage) {
        this.preferredLanguage = preferredLanguage;
    }

    @Override
    public String toString() {
        return Utils.jsonSerialize(this, true);
    }
}
