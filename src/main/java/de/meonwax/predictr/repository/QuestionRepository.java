package de.meonwax.predictr.repository;

import org.springframework.data.jpa.repository.JpaRepository;

import de.meonwax.predictr.domain.Question;

public interface QuestionRepository extends JpaRepository<Question, Long> {
}
