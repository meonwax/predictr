package de.meonwax.repository;

import org.springframework.data.jpa.repository.JpaRepository;

import de.meonwax.domain.Group;

public interface GroupRepository extends JpaRepository<Group, String> {
}
