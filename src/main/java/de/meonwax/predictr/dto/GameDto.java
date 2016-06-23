package de.meonwax.predictr.dto;

import javax.validation.constraints.NotNull;

import de.meonwax.predictr.domain.Team;
import de.meonwax.predictr.util.Utils;

public class GameDto {

    @NotNull
    private Long id;

    private Team teamHome;

    private Team teamAway;

    private Integer scoreHome;

    private Integer scoreAway;

    private String notes;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Team getTeamHome() {
        return teamHome;
    }

    public void setTeamHome(Team teamHome) {
        this.teamHome = teamHome;
    }

    public Team getTeamAway() {
        return teamAway;
    }

    public void setTeamAway(Team teamAway) {
        this.teamAway = teamAway;
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

    public String getNotes() {
        return notes;
    }

    public void setNotes(String notes) {
        this.notes = notes;
    }

    @Override
    public String toString() {
        return Utils.jsonSerialize(this, true);
    }
}
