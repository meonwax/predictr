package de.meonwax.predictr.domain;

import java.io.Serializable;
import java.time.ZonedDateTime;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import javax.persistence.ManyToOne;
import javax.validation.constraints.NotNull;

@Entity
public class Shout implements Serializable {

    private static final long serialVersionUID = 1L;

    public Shout() {
    }

    public Shout(ZonedDateTime date, String message, User user) {
        this.date = date;
        this.message = message;
        this.user = user;
    }

    @Id
    @GeneratedValue
    private Long id;

    @NotNull
    @Column(nullable = false)
    private ZonedDateTime date;

    @NotNull
    @Column(nullable = false)
    private String message;

    @NotNull
    @ManyToOne(optional = false)
    private User user;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public ZonedDateTime getDate() {
        return date;
    }

    public void setDate(ZonedDateTime date) {
        this.date = date;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public User getUser() {
        return user;
    }

    public void setUser(User user) {
        this.user = user;
    }
}
