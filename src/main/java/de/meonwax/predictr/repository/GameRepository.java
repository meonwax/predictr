package de.meonwax.predictr.repository;

import de.meonwax.predictr.domain.Game;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;

@Repository
public interface GameRepository extends JpaRepository<Game, Long> {

    List<Game> findByKickoffTimeAfterOrderByKickoffTime(Pageable pageable, Instant dateTime);

    // TODO: Implement as custom query with @Query
    List<Game> findByKickoffTimeBeforeAndScoreHomeIsNullAndScoreAwayIsNullOrderByKickoffTime(Instant dateTime);

    Long countByScoreHomeIsNotNullAndScoreAwayIsNotNull();
}
