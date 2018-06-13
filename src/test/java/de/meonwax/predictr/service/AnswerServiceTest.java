package de.meonwax.predictr.service;

import de.meonwax.predictr.domain.Answer;
import de.meonwax.predictr.domain.Question;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.dto.AnswerDto;
import de.meonwax.predictr.repository.AnswerRepository;
import de.meonwax.predictr.repository.QuestionRepository;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Captor;
import org.mockito.Mock;
import org.mockito.junit.MockitoJUnitRunner;

import java.time.Clock;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import static org.hamcrest.CoreMatchers.is;
import static org.hamcrest.MatcherAssert.assertThat;
import static org.mockito.Mockito.*;

@RunWith(MockitoJUnitRunner.class)
public class AnswerServiceTest {

    private AnswerService service;

    @Mock
    private AnswerRepository answerRepositoryMock;

    @Mock
    private QuestionRepository questionRepositoryMock;

    @Mock
    private CalculationService calculationServiceMock;

    private Clock clock;

    @Captor
    private ArgumentCaptor<List<Answer>> captor;

    @Before
    public void setUp() {
        clock = Clock.systemUTC();
        service = new AnswerService(answerRepositoryMock, questionRepositoryMock, calculationServiceMock, clock);
    }

    @Test
    public void update() {
        User user = new User();
        List<AnswerDto> answers = new ArrayList<>();
        answers.add(createAnswer(1L, Instant.now(clock).plus(1, ChronoUnit.SECONDS)));
        answers.add(createAnswer(2L, Instant.now(clock).plus(2, ChronoUnit.DAYS)));
        answers.add(createAnswer(3L, Instant.now(clock).minus(1, ChronoUnit.SECONDS)));
        answers.add(createAnswer(4L, Instant.now(clock).minus(3, ChronoUnit.DAYS)));
        answers.add(createAnswer(5L, Instant.now(clock).plus(2, ChronoUnit.HOURS)));

        service.update(user, answers);

        verify(answerRepositoryMock, times(1)).saveAll(captor.capture());

        List<Answer> actual = captor.getValue();
        assertThat(actual.size(), is(3));
    }

    private AnswerDto createAnswer(Long id, Instant deadline) {
        Question question = new Question();
        question.setId(id);
        question.setDeadline(deadline);
        AnswerDto answer = new AnswerDto();
        answer.setQuestion(question);
        when(questionRepositoryMock.findById(id))
            .thenReturn(Optional.of(question));
        return answer;
    }
}
