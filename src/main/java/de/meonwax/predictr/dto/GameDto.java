package de.meonwax.predictr.dto;

import de.meonwax.predictr.domain.Team;
import lombok.Data;

import javax.validation.constraints.NotNull;

@Data
public class GameDto {

    @NotNull
    private Long id;

    private Team teamHome;

    private Team teamAway;

    private Integer scoreHome;

    private Integer scoreAway;

    private String notes;
}
