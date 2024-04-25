package de.meonwax.predictr.domain;

import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Data;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.ManyToOne;
import javax.validation.constraints.NotNull;

@Data
@Entity
public class Team {

    @Id
    @Column(length = 3)
    private String id;

    @NotNull
    @ManyToOne(optional = false)
    @JsonIgnore
    private Group group;
}
