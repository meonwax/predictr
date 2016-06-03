package de.meonwax.predictr.service;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;

import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import de.meonwax.predictr.domain.Answer;
import de.meonwax.predictr.domain.Question;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.dto.QuestionDto;
import de.meonwax.predictr.repository.QuestionRepository;

@Service
public class QuestionService {

    @Autowired
    private QuestionRepository questionRepository;

    @Autowired
    private CalculationService calculationService;

    public void update(List<QuestionDto> questionDtos) {
        List<Question> questions = new ArrayList<>();
        for (QuestionDto questionDto : questionDtos) {
            Question question = questionRepository.findOne(questionDto.getId());
            if (question == null) {
                question = new Question();
            }
            BeanUtils.copyProperties(questionDto, question);
            questions.add(question);
        }
        questionRepository.save(questions);
    }

    public List<Question> getAllWithUsersAnswers(User user) {
        List<Question> questions = questionRepository.findAll();
        for (Question question : questions) {
            if (question.getAnswers().size() > 0) {

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
                    question.setPointsEarned(calculationService.calculate(question.getAnswers().iterator().next()));
                    // Set only user's answer to result
                    question.setAnswers(new HashSet<Answer>(Arrays.asList(usersAnswer)));
                } else {
                    // Delete all bets from result
                    question.setAnswers(new HashSet<Answer>());
                }
            }
        }
        return questions;
    }
}
