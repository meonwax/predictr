package de.meonwax.predictr.repository;

import de.meonwax.predictr.domain.Answer;
import de.meonwax.predictr.domain.Question;
import de.meonwax.predictr.domain.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;

@Repository
public interface AnswerRepository extends JpaRepository<Answer, Long> {

    List<Answer> findByUserAndQuestionDeadlineBefore(User user, Instant dateTime);

    Answer findOneByUserAndQuestion(User user, Question question);
}
