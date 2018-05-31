package de.meonwax.predictr.dto;

import lombok.Data;

import javax.persistence.Column;
import javax.validation.constraints.NotNull;

@Data
public class ShoutDto {

    @NotNull
    @Column(nullable = false)
    private String message;
}
