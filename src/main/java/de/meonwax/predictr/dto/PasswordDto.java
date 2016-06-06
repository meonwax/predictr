package de.meonwax.predictr.dto;

import javax.validation.constraints.NotNull;
import javax.validation.constraints.Size;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonProperty.Access;

import de.meonwax.predictr.util.Utils;

public class PasswordDto {

    @NotNull
    @Size(min = 5, max = 100)
    @JsonProperty(access = Access.WRITE_ONLY)
    private String oldPassword;

    @NotNull
    @Size(min = 5, max = 100)
    @JsonProperty(access = Access.WRITE_ONLY)
    private String newPassword;

    public String getOldPassword() {
        return oldPassword;
    }

    public void setOldPassword(String oldPassword) {
        this.oldPassword = oldPassword;
    }

    public String getNewPassword() {
        return newPassword;
    }

    public void setNewPassword(String newPassword) {
        this.newPassword = newPassword;
    }

    @Override
    public String toString() {
        return Utils.jsonSerialize(this, true);
    }
}
