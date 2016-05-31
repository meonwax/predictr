package de.meonwax.predictr.domain;

import java.io.Serializable;

import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.ManyToOne;
import javax.validation.constraints.NotNull;

import com.fasterxml.jackson.annotation.JsonIgnore;

@Entity
public class Team implements Serializable {

    private static final long serialVersionUID = 1L;

	@Id
	private String id;

	@NotNull
	@ManyToOne(optional = false)
    @JsonIgnore
	private Group group;

	public String getId() {
		return id;
	}

	public void setId(String id) {
		this.id = id;
	}

	public Group getGroup() {
		return group;
	}

	public void setGroup(Group group) {
		this.group = group;
	}
}
