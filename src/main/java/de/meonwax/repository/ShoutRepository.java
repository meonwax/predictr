package de.meonwax.repository;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import de.meonwax.domain.Shout;

public interface ShoutRepository extends JpaRepository<Shout, Long> {

    public Page<Shout> findAllByOrderByDateDesc(Pageable pageable);
}
