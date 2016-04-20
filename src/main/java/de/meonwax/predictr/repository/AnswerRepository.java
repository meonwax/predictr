package de.meonwax.predictr.repository;

import java.time.ZonedDateTime;
import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

import de.meonwax.predictr.domain.Answer;
import de.meonwax.predictr.domain.Question;
import de.meonwax.predictr.domain.User;

public interface AnswerRepository extends JpaRepository<Answer, Long> {

    List<Answer> findByUserAndQuestionDeadlineBefore(User user, ZonedDateTime dateTime);

    Answer findOneByUserAndQuestion(User user, Question question);
}
