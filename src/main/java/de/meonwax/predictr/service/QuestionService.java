package de.meonwax.predictr.service;

import java.util.ArrayList;
import java.util.List;

import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

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

    public List<Question> getAllWithUsersAnswers(User user) {
        List<Question> questions = questionRepository.findAllWithUsersAnswers(user);
        for( Question question : questions) {
            if( question.getAnswers().size() > 0 ) {
                question.setPointsEarned(calculationService.calculate(question.getAnswers().iterator().next()));
            }
        }
        return questions;
    }

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
}
