package de.meonwax.predictr.repository;

import org.springframework.data.jpa.repository.JpaRepository;

import de.meonwax.predictr.domain.Avatar;

public interface AvatarRepository extends JpaRepository<Avatar, Long> {
}
