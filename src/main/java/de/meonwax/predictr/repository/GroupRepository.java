package de.meonwax.predictr.repository;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import de.meonwax.predictr.domain.Group;
import de.meonwax.predictr.domain.User;

public interface GroupRepository extends JpaRepository<Group, String> {

    @Query("SELECT DISTINCT g FROM Group g LEFT JOIN FETCH g.games games LEFT JOIN FETCH games.bets bets WHERE bets.user = :user OR bets.user IS NULL ORDER BY g.priority")
    List<Group> findAllWithUsersBets(@Param("user") User user);
}
