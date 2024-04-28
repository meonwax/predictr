package de.meonwax.predictr.domain;

import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Data;

import javax.persistence.*;
import javax.validation.constraints.NotNull;
import java.util.Set;

@Data
@Entity
// 'group' is a reserved word in H2 database
@Table(name = "groups")
public class Group {

    @Id
    @Column(length = 1)
    private String id;

    @NotNull
    @Column(nullable = false)
    private Integer priority;

    @OneToMany(mappedBy = "group")
    @JsonIgnore
    private Set<Team> teams;

    @OneToMany(mappedBy = "group")
    @OrderBy("kickoffTime ASC")
    private Set<Game> games;
}
