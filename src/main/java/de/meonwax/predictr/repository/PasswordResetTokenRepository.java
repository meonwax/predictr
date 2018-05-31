package de.meonwax.predictr.repository;

import de.meonwax.predictr.domain.PasswordResetToken;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PasswordResetTokenRepository extends JpaRepository<PasswordResetToken, Long> {

    PasswordResetToken findOneByValue(String value);
}
