package de.meonwax.predictr.repository;

import de.meonwax.predictr.domain.RememberMeToken;
import de.meonwax.predictr.domain.User;
import org.springframework.data.jpa.repository.JpaRepository;

public interface RememberMeTokenRepository extends JpaRepository<RememberMeToken, String> {

    Long deleteByUser(User user);
}
