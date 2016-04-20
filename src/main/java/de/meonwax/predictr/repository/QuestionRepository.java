package de.meonwax.predictr.repository;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import de.meonwax.predictr.domain.Question;
import de.meonwax.predictr.domain.User;

public interface QuestionRepository extends JpaRepository<Question, Long> {

    @Query("SELECT question FROM Question question LEFT JOIN FETCH question.answers answers WHERE answers.user = :user OR answers.user IS NULL")
    List<Question> findAllWithUsersAnswers(@Param("user") User user);
}
