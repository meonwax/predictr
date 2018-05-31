package de.meonwax.predictr.repository;

import de.meonwax.predictr.domain.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.util.List;

@Repository
public interface UserRepository extends JpaRepository<User, Long> {

    List<User> findAllByOrderByCreatedDateDesc();

    List<User> findByWagerGreaterThan(BigDecimal wager);

    @Query(value = "SELECT SUM(wager) FROM user", nativeQuery = true)
    BigDecimal getFullJackpot();

    User findOneByEmailIgnoringCase(String email);
}
