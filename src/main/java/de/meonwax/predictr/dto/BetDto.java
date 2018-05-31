package de.meonwax.predictr.dto;

import de.meonwax.predictr.domain.Game;
import de.meonwax.predictr.domain.User;
import lombok.Data;

import javax.validation.constraints.NotNull;

@Data
public class BetDto {

    @NotNull
    private Game game;

    @NotNull
    private Integer scoreHome;

    @NotNull
    private Integer scoreAway;

    private User user;

    private String cssClass;
}
