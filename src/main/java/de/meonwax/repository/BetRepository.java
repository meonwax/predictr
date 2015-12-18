package de.meonwax.repository;

import java.time.ZonedDateTime;
import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

import de.meonwax.domain.Bet;
import de.meonwax.domain.User;

public interface BetRepository extends JpaRepository<Bet, Long> {

    List<Bet> findByUserAndGameKickoffTimeBefore(User user, ZonedDateTime dateTime);
}
