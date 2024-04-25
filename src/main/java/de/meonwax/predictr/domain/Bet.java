package de.meonwax.predictr.domain;

import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Data;

import javax.persistence.*;
import javax.validation.constraints.NotNull;

@Data
@Entity
@Table(uniqueConstraints = @UniqueConstraint(columnNames = {"user_id", "game_id"}))
public class Bet {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @NotNull
    @ManyToOne(optional = false)
    @JsonIgnore
    private User user;

    @NotNull
    @ManyToOne(optional = false)
    @JsonIgnore
    private Game game;

    private Integer scoreHome;

    private Integer scoreAway;
}
