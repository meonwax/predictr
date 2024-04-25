package de.meonwax.predictr.domain;

import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Data;

import javax.persistence.*;
import javax.validation.constraints.NotNull;
import java.time.Instant;
import java.util.Set;

@Entity
@Data
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
}
