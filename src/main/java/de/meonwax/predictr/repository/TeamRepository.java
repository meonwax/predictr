package de.meonwax.predictr.repository;

import org.springframework.data.jpa.repository.JpaRepository;

import de.meonwax.predictr.domain.Team;

public interface TeamRepository extends JpaRepository<Team, String> {
}
