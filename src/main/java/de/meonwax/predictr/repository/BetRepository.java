package de.meonwax.predictr.repository;

import java.time.ZonedDateTime;
import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

import de.meonwax.predictr.domain.Bet;
import de.meonwax.predictr.domain.Game;
import de.meonwax.predictr.domain.User;

public interface BetRepository extends JpaRepository<Bet, Long> {

    List<Bet> findByUserAndGameKickoffTimeBefore(User user, ZonedDateTime dateTime);

    Bet findOneByUserAndGame(User user, Game game);
}
