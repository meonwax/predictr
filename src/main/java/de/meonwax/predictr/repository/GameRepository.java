package de.meonwax.predictr.repository;

import java.time.ZonedDateTime;
import java.util.List;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import de.meonwax.predictr.domain.Game;

public interface GameRepository extends JpaRepository<Game, Long> {

    List<Game> findByKickoffTimeAfterOrderByKickoffTime(Pageable pageable, ZonedDateTime dateTime);

    // TODO: Implement as custom query with @Query
    List<Game> findByKickoffTimeBeforeAndScoreHomeIsNullAndScoreAwayIsNullOrderByKickoffTime(ZonedDateTime dateTime);
}
