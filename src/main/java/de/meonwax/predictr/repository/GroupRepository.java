package de.meonwax.predictr.repository;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import de.meonwax.predictr.domain.Group;

public interface GroupRepository extends JpaRepository<Group, String> {

    @Query("SELECT DISTINCT g FROM Group g LEFT JOIN FETCH g.games games ORDER BY g.priority ASC")
    List<Group> findAllWithGames();
}
