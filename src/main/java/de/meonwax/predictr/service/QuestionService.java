package de.meonwax.predictr.service;

import de.meonwax.predictr.domain.Answer;
import de.meonwax.predictr.domain.Question;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.dto.QuestionDto;
import de.meonwax.predictr.repository.QuestionRepository;
import lombok.AllArgsConstructor;
import org.springframework.beans.BeanUtils;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;

@Service
@AllArgsConstructor
public class QuestionService {

    private final QuestionRepository questionRepository;

    private final CalculationService calculationService;

    public void update(List<QuestionDto> questionDtos) {
        List<Question> questions = new ArrayList<>();
        for (QuestionDto questionDto : questionDtos) {
            Question question = questionRepository
                .findById(questionDto.getId())
                .orElseGet(Question::new);
            BeanUtils.copyProperties(questionDto, question);
            questions.add(question);
        }
        questionRepository.saveAll(questions);
    }

    public List<Question> getAllWithUsersAnswers(User user) {
        List<Question> questions = questionRepository.findAll();
        for (Question question : questions) {
            if (!question.getAnswers().isEmpty()) {

                // Fetch user's answer
                Answer usersAnswer = null;
                for (Answer answer : question.getAnswers()) {
                    if (answer.getUser().equals(user)) {
                        usersAnswer = answer;
                        break;
                    }
                }

                if (usersAnswer != null) {
                    // Calculate points
                    question.setPointsEarned(calculationService.calculate(usersAnswer));
                    // Set only user's answer to result
                    question.setAnswers(new HashSet<>(Collections.singletonList(usersAnswer)));
                } else {
                    // Delete all bets from result
                    question.setAnswers(new HashSet<>());
                }
            }
        }
        return questions;
    }
}
