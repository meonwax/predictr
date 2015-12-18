package de.meonwax.repository;

import java.time.ZonedDateTime;
import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

import de.meonwax.domain.Answer;
import de.meonwax.domain.User;

public interface AnswerRepository extends JpaRepository<Answer, Long> {

    List<Answer> findByUserAndQuestionDeadlineBefore(User user, ZonedDateTime dateTime);
}
