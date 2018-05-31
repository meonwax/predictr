package de.meonwax.predictr.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonProperty.Access;
import lombok.Data;

import javax.validation.constraints.NotNull;
import javax.validation.constraints.Size;

@Data
public class PasswordDto {

    @NotNull
    @Size(min = 5, max = 100)
    @JsonProperty(access = Access.WRITE_ONLY)
    private String oldPassword;

    @NotNull
    @Size(min = 5, max = 100)
    @JsonProperty(access = Access.WRITE_ONLY)
    private String newPassword;
}
