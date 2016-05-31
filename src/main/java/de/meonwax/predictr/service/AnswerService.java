package de.meonwax.predictr.service;

import java.time.ZonedDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import de.meonwax.predictr.domain.Answer;
import de.meonwax.predictr.domain.Question;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.dto.AnswerDto;
import de.meonwax.predictr.repository.AnswerRepository;
import de.meonwax.predictr.repository.QuestionRepository;

@Service
public class AnswerService {

    private final Logger log = LoggerFactory.getLogger(AnswerService.class);

    @Autowired
    private AnswerRepository answerRepository;

    @Autowired
    private QuestionRepository questionRepository;

    public void update(User user, List<AnswerDto> answerDtos) {
        List<Answer> answers = new ArrayList<>();
        for (AnswerDto answerDto : answerDtos) {
            // TODO: Prevent saving if deadline has already passed
            Answer answer = answerRepository.findOneByUserAndQuestion(user, answerDto.getQuestion());
            if (answer == null) {
                answer = new Answer();
            }
            BeanUtils.copyProperties(answerDto, answer);
            answer.setUser(user);
            answers.add(answer);
        }
        answerRepository.save(answers);
    }

    public Optional<List<AnswerDto>> getOther(User ownUser, Long questionId) {

        Question question = questionRepository.findOne(questionId);

        // Only return data if deadline has already passed
        if (question == null || question.getDeadline().isAfter(ZonedDateTime.now())) {
            return Optional.empty();
        }

        // Build the result
        List<AnswerDto> result = new ArrayList<>();
        for (Answer answer : question.getAnswers()) {
            // Filter out own user
            if (!answer.getUser().equals(ownUser)) {
                AnswerDto dto = new AnswerDto();
                dto.setUser(answer.getUser());
                dto.setAnswer(answer.getAnswer());
                result.add(dto);
            }
        }
        return Optional.of(result);
    }
}
