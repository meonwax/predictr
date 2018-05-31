package de.meonwax.predictr.repository;

import org.springframework.data.jpa.repository.JpaRepository;

import de.meonwax.predictr.domain.Question;
import org.springframework.stereotype.Repository;

@Repository
public interface QuestionRepository extends JpaRepository<Question, Long> {
}
