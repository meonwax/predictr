package de.meonwax.predictr.dto;

import javax.validation.constraints.NotNull;

import de.meonwax.predictr.util.Utils;

public class GameDto {

    @NotNull
    private Long id;

    @NotNull
    private Integer scoreHome;

    @NotNull
    private Integer scoreAway;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
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
        return Utils.jsonSerialize(this, true);
    }
}