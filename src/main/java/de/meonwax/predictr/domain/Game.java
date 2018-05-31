package de.meonwax.predictr.domain;

import com.fasterxml.jackson.annotation.JsonIgnore;
import de.meonwax.predictr.util.Utils;

import javax.persistence.*;
import javax.validation.constraints.NotNull;
import java.time.ZonedDateTime;
import java.util.Set;

@Entity
public class Game {

    @Id
    private Long id;

    @NotNull
    @Column(nullable = false)
    private ZonedDateTime kickoffTime;

    @NotNull
    @ManyToOne(optional = false)
    @JsonIgnore
    private Group group;

    @NotNull
    @ManyToOne(optional = false)
    private Location location;

    @ManyToOne
    private Team teamHome;

    @ManyToOne
    private Team teamAway;

    private Integer scoreHome;

    private Integer scoreAway;

    private String notes;

    @Transient
    private Integer pointsEarned;

    @OneToMany(mappedBy = "game")
    private Set<Bet> bets;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public ZonedDateTime getKickoffTime() {
        return kickoffTime;
    }

    public void setKickoffTime(ZonedDateTime kickoffTime) {
        this.kickoffTime = kickoffTime;
    }

    public Group getGroup() {
        return group;
    }

    public void setGroup(Group group) {
        this.group = group;
    }

    public Location getLocation() {
        return location;
    }

    public void setLocation(Location location) {
        this.location = location;
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

    public Integer getPointsEarned() {
        return pointsEarned;
    }

    public void setPointsEarned(Integer pointsEarned) {
        this.pointsEarned = pointsEarned;
    }

    public Set<Bet> getBets() {
        return bets;
    }

    public void setBets(Set<Bet> bets) {
        this.bets = bets;
    }

    @Override
    public String toString() {
        return Utils.jsonSerialize(this, true);
    }
}
