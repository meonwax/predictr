package de.meonwax.repository;

import java.math.BigDecimal;
import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import de.meonwax.domain.User;

public interface UserRepository extends JpaRepository<User, Long> {

    public List<User> findByWagerGreaterThan(BigDecimal wager);

    @Query(value = "SELECT SUM(wager) FROM user", nativeQuery = true)
    public BigDecimal getJackpot();

    public User findOneByEmailIgnoringCase(String email);
}
