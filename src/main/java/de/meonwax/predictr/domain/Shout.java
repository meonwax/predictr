package de.meonwax.predictr.domain;

import lombok.Data;
import lombok.NoArgsConstructor;

import javax.persistence.*;
import javax.validation.constraints.NotNull;
import java.time.Instant;

@Data
@NoArgsConstructor
@Entity
public class Shout {

    public Shout(Instant date, String message, User user) {
        this.date = date;
        this.message = message;
        this.user = user;
    }

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @NotNull
    @Column(nullable = false)
    private Instant date;

    @NotNull
    @Column(nullable = false)
    private String message;

    @NotNull
    @ManyToOne(optional = false)
    private User user;
}
