package de.meonwax.predictr.dto;

import javax.validation.constraints.NotNull;

import de.meonwax.predictr.domain.Game;

public class BetDto {

    @NotNull
    private Game game;

    @NotNull
    private Integer scoreHome;

    @NotNull
    private Integer scoreAway;

    public Game getGame() {
        return game;
    }

    public void setGame(Game game) {
        this.game = game;
    }

    public Integer getScoreHome() {
        return scoreHome;
    }

    public void setScoreHome(Integer scoreHome) {
        this.scoreHome = scoreHome;
    }

    public Integer getScoreAway() {
        return scoreAway;
    }

    public void setScoreAway(Integer scoreAway) {
        this.scoreAway = scoreAway;
    }

    @Override
    public String toString() {
        return "BetDto [game=" + game + ", scoreHome=" + scoreHome + ", scoreAway=" + scoreAway + "]";
    }
}
