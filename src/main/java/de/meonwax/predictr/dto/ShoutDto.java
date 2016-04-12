package de.meonwax.predictr.dto;

import javax.persistence.Column;
import javax.validation.constraints.NotNull;

public class ShoutDto {

    @NotNull
    @Column(nullable = false)
    private String message;

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }
}
