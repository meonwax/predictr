package de.meonwax.predictr.service;

import java.util.ArrayList;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import de.meonwax.predictr.domain.Answer;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.dto.AnswerDto;
import de.meonwax.predictr.repository.AnswerRepository;

@Service
public class AnswerService {

    private final Logger log = LoggerFactory.getLogger(AnswerService.class);

    @Autowired
    private AnswerRepository answerRepository;

    public void update(User user, List<AnswerDto> answerDtos) {
        List<Answer> answers = new ArrayList<>();
        for (AnswerDto answerDto : answerDtos) {
            // TODO: Prevent saving if tournament has already started
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
}
