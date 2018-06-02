package de.meonwax.predictr.domain;

import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.ToString;

import javax.persistence.*;
import javax.validation.constraints.NotNull;
import java.time.Instant;
import java.util.Set;

@Entity
@ToString
public class Game {

    @Id
    private Long id;

    @NotNull
    @Column(nullable = false)
    private Instant kickoffTime;

    @NotNull
    @ManyToOne(optional = false)
    @JsonIgnore
    private Group group;

    @NotNull
    @ManyToOne(optional = false)
    private Venue venue;

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

    public Instant getKickoffTime() {
        return kickoffTime;
    }

    public void setKickoffTime(Instant kickoffTime) {
        this.kickoffTime = kickoffTime;
    }

    public Group getGroup() {
        return group;
    }

    public void setGroup(Group group) {
        this.group = group;
    }

    public Venue getVenue() {
        return venue;
    }

    public void setVenue(Venue venue) {
        this.venue = venue;
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
}
