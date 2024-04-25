package de.meonwax.predictr.domain;

import lombok.Data;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.Id;
import javax.validation.constraints.NotNull;

@Data
@Entity
public class Venue {

    @Id
    private Long id;

    @NotNull
    @Column(nullable = false)
    private String stadium;

    @NotNull
    @Column(nullable = false)
    private String city;
}
