package de.meonwax.predictr.repository;

import java.math.BigDecimal;
import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import de.meonwax.predictr.domain.User;

public interface UserRepository extends JpaRepository<User, Long> {

    public List<User> findByWagerGreaterThan(BigDecimal wager);

    @Query(value = "SELECT SUM(wager) FROM user", nativeQuery = true)
    public BigDecimal getFullJackpot();

    public User findOneByEmailIgnoringCase(String email);
}
