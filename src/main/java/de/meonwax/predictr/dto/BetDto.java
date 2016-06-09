package de.meonwax.predictr.dto;

import javax.validation.constraints.NotNull;

import de.meonwax.predictr.domain.Game;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.util.Utils;

public class BetDto {

    @NotNull
    private Game game;

    @NotNull
    private Integer scoreHome;

    @NotNull
    private Integer scoreAway;

    private User user;

    private String cssClass;

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

    public User getUser() {
        return user;
    }

    public void setUser(User user) {
        this.user = user;
    }

    public String getCssClass() {
        return cssClass;
    }

    public void setCssClass(String cssClass) {
        this.cssClass = cssClass;
    }

    @Override
    public String toString() {
        return Utils.jsonSerialize(this, true);
    }
}
