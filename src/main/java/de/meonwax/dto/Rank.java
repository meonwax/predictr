package de.meonwax.dto;

import java.io.Serializable;

import de.meonwax.domain.User;

public class Rank implements Serializable {

    private static final long serialVersionUID = 1L;

    private User user;

    private Integer points;

    private Integer position;

    public Rank(User user, Integer points, Integer position) {
        this.user = user;
        this.points = points;
        this.position = position;
    }

    public User getUser() {
        return user;
    }

    public Integer getPoints() {
        return points;
    }

    public Integer getPosition() {
        return position;
    }
}
