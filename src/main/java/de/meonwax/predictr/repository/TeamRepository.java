package de.meonwax.predictr.repository;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

import de.meonwax.predictr.domain.Team;

public interface TeamRepository extends JpaRepository<Team, String> {

    public List<Team> findAllByOrderById();
}
