package de.meonwax.predictr.repository;

import org.springframework.data.jpa.repository.JpaRepository;

import de.meonwax.predictr.domain.RememberMeToken;
import de.meonwax.predictr.domain.User;

public interface RememberMeTokenRepository extends JpaRepository<RememberMeToken, String> {

    public Long deleteByUser(User user);
}
