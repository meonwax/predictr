package de.meonwax.predictr.domain;

import java.io.Serializable;

import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import javax.persistence.ManyToOne;
import javax.persistence.Table;
import javax.persistence.UniqueConstraint;
import javax.validation.constraints.NotNull;

import com.fasterxml.jackson.annotation.JsonIgnore;

@Entity
@Table(uniqueConstraints = @UniqueConstraint(columnNames = { "user_id", "game_id" }))
public class Bet implements Serializable {

    private static final long serialVersionUID = 1L;

    @Id
    @GeneratedValue
    private Long id;

    @NotNull
    @ManyToOne(optional = false)
    @JsonIgnore
    private User user;

    @NotNull
    @ManyToOne(optional = false)
    private Game game;

    private Integer scoreHome;

    private Integer scoreAway;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public User getUser() {
        return user;
    }

    public void setUser(User user) {
        this.user = user;
    }

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
}
