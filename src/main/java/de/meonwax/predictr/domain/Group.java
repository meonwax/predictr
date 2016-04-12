package de.meonwax.predictr.domain;

import java.io.Serializable;
import java.util.Set;

import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.OneToMany;
import javax.persistence.OrderBy;
import javax.persistence.Table;

import com.fasterxml.jackson.annotation.JsonIgnore;

@Entity
// Unfortunately 'group' is a reserved word in H2 database
@Table(name = "groups")
public class Group implements Serializable {

    private static final long serialVersionUID = 1L;

    @Id
    private String id;

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
