package de.meonwax.predictr.dto;

import lombok.Data;

import javax.validation.constraints.NotNull;
import javax.validation.constraints.Size;

@Data
public class UserDataDto {

    @NotNull
    @Size(max = 255)
    private String name;

    @NotNull
    @Size(min = 2, max = 2)
    private String preferredLanguage;
}
