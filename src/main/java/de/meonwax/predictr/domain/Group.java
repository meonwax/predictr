package de.meonwax.predictr.domain;

import com.fasterxml.jackson.annotation.JsonIgnore;

import javax.persistence.*;
import javax.validation.constraints.NotNull;
import java.util.Set;

@Entity
// Unfortunately 'group' is a reserved word in H2 database
@Table(name = "groups")
public class Group {

    @Id
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

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public Integer getPriority() {
        return priority;
    }

    public void setPriority(Integer priority) {
        this.priority = priority;
    }

    public Set<Team> getTeams() {
        return teams;
    }

    public void setTeams(Set<Team> teams) {
        this.teams = teams;
    }

    public Set<Game> getGames() {
        return games;
    }

    public void setGames(Set<Game> games) {
        this.games = games;
    }
}
