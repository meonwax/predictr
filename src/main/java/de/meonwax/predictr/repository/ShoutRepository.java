package de.meonwax.predictr.repository;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import de.meonwax.predictr.domain.Shout;
import org.springframework.stereotype.Repository;

@Repository
public interface ShoutRepository extends JpaRepository<Shout, Long> {

    Page<Shout> findAllByOrderByDateDesc(Pageable pageable);
}
