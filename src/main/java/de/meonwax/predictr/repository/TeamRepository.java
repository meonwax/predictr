package de.meonwax.predictr.repository;

import de.meonwax.predictr.domain.Team;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface TeamRepository extends JpaRepository<Team, String> {

    List<Team> findAllByOrderById();
}
