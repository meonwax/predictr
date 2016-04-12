package de.meonwax.predictr.repository;

import org.springframework.data.jpa.repository.JpaRepository;

import de.meonwax.predictr.domain.Group;

public interface GroupRepository extends JpaRepository<Group, String> {
}
