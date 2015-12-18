package de.meonwax.repository;

import org.springframework.data.jpa.repository.JpaRepository;

import de.meonwax.domain.Shout;

public interface ShoutRepository extends JpaRepository<Shout, Long> {
}
