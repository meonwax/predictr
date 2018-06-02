package de.meonwax.predictr.service;

import de.meonwax.predictr.domain.Answer;
import de.meonwax.predictr.domain.Question;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.dto.AnswerDto;
import de.meonwax.predictr.repository.AnswerRepository;
import de.meonwax.predictr.repository.QuestionRepository;
import lombok.AllArgsConstructor;
import org.springframework.beans.BeanUtils;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

@Service
@AllArgsConstructor
public class AnswerService {

    private final AnswerRepository answerRepository;

    private final QuestionRepository questionRepository;

    private final CalculationService calculationService;

    public void update(User user, List<AnswerDto> answerDtos) {
        List<Answer> answers = new ArrayList<>();
        for (AnswerDto answerDto : answerDtos) {
            questionRepository.findById(answerDto.getQuestion().getId())
                .ifPresent(question -> {
                    // Prevent saving if deadline has already passed
                    if (question.getDeadline().isAfter(Instant.now())) {
                        Answer answer = answerRepository.findOneByUserAndQuestion(user, question);
                        if (answer == null) {
                            answer = new Answer();
                        }
                        BeanUtils.copyProperties(answerDto, answer);
                        answer.setUser(user);
                        answers.add(answer);
                    }
                });

            answerRepository.saveAll(answers);
        }
    }

    public Optional<List<AnswerDto>> getOther(User ownUser, Long questionId) {

        Optional<Question> question = questionRepository.findById(questionId);

        // Only return data if deadline has already passed
        if (!question.isPresent() || question.get().getDeadline().isAfter(Instant.now())) {
            return Optional.empty();
        }

        // Build the result
        List<AnswerDto> result = new ArrayList<>();
        for (Answer answer : question.get().getAnswers()) {
            // Filter out own user
            if (!answer.getUser().equals(ownUser)) {
                AnswerDto dto = new AnswerDto();
                dto.setUser(answer.getUser());
                dto.setAnswer(answer.getAnswer());
                dto.setCssClass(calculationService.getCssClass(answer));
                result.add(dto);
            }
        }
        return Optional.of(result);
    }
}
