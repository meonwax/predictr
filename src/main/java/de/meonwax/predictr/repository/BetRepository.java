package de.meonwax.predictr.repository;

import de.meonwax.predictr.domain.Bet;
import de.meonwax.predictr.domain.Game;
import de.meonwax.predictr.domain.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

@Repository
public interface BetRepository extends JpaRepository<Bet, Long> {

    List<Bet> findByUserAndGameKickoffTimeBefore(User user, Instant dateTime);

    Optional<Bet> findOneByUserAndGame(User user, Game game);
}
