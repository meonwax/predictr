package de.meonwax.predictr.service;

import de.meonwax.predictr.domain.*;
import de.meonwax.predictr.repository.AnswerRepository;
import de.meonwax.predictr.repository.BetRepository;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.Mock;
import org.mockito.junit.MockitoJUnitRunner;

import java.time.Clock;
import java.util.Arrays;
import java.util.List;

import static org.hamcrest.CoreMatchers.is;
import static org.hamcrest.MatcherAssert.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

@RunWith(MockitoJUnitRunner.class)
public class CalculationServiceTest {

    @Mock
    private ConfigService configServiceMock;

    @Mock
    private BetRepository betRepositoryMock;

    @Mock
    private AnswerRepository answerRepositoryMock;

    private CalculationService service;

    @Before
    public void setUp() {
        service = new CalculationService(configServiceMock, betRepositoryMock, answerRepositoryMock, Clock.systemUTC());
        Config config = new Config();
        config.setPointsResult(5);
        config.setPointsTendency(2);
        config.setPointsTendencySpread(3);
        when(configServiceMock.getConfig())
            .thenReturn(config);
    }

    @Test
    public void calculateBetResult() {
        Bet bet = createBet(1, 2, 1, 2);
        int result = service.calculate(bet);
        assertThat(result, is(5));
    }

    @Test
    public void calculateBetTendancy() {
        Bet bet = createBet(1, 2, 0, 8);
        int result = service.calculate(bet);
        assertThat(result, is(2));
    }

    @Test
    public void calculateBetTendancySpread() {
        Bet bet = createBet(0, 0, 1, 1);
        int result = service.calculate(bet);
        assertThat(result, is(3));
    }

    @Test
    public void calculateBetWrong() {
        Bet bet = createBet(2, 1, 0, 0);
        int result = service.calculate(bet);
        assertThat(result, is(0));
    }

    @Test
    public void calculateBetMissingField() {
        Bet bet = createBet(0, 0, 0, 0);
        bet.setScoreAway(null);
        int result = service.calculate(bet);
        assertThat(result, is(0));
    }


    @Test
    public void calculateAnswerCorrect() {
        Answer answer = createAnswer("Alex Meier", "Alex Meier", 10);
        int result = service.calculate(answer);
        assertThat(result, is(10));

        answer = createAnswer("Meier", "Alex Meier, Meier, Alexander Meier", 5);
        result = service.calculate(answer);
        assertThat(result, is(5));
    }

    @Test
    public void calculateAnswerWrong() {
        Answer answer = createAnswer("Mario Götze", "Alex Meier", 10);
        int result = service.calculate(answer);
        assertThat(result, is(0));
    }

    @Test
    public void getPoints() {
        List<Bet> bets = Arrays.asList(
            createBet(0, 0, 0, 0),
            createBet(1, 2, 2, 3),
            createBet(0, 0, 1, 2)
        );
        when(betRepositoryMock.findByUserAndGameKickoffTimeBefore(any(), any()))
            .thenReturn(bets);

        List<Answer> answers = Arrays.asList(
            createAnswer("Meier", "Meier", 5),
            createAnswer("Meier", "Wimmer", 5)
        );
        when(answerRepositoryMock.findByUserAndQuestionDeadlineBefore(any(), any()))
            .thenReturn(answers);

        int result = service.getPoints(new User());

        assertThat(result, is(13));
    }

    private Bet createBet(int betHome, int betAway, int resultHome, int resultAway) {
        Game game = new Game();
        game.setScoreHome(resultHome);
        game.setScoreAway(resultAway);
        Bet bet = new Bet();
        bet.setGame(game);
        bet.setScoreHome(betHome);
        bet.setScoreAway(betAway);
        return bet;
    }

    private Answer createAnswer(String userAnswer, String correctAnswer, int points) {
        Question question = new Question();
        question.setCorrectAnswer(correctAnswer);
        question.setPoints(points);
        Answer answer = new Answer();
        answer.setQuestion(question);
        answer.setAnswer(userAnswer);
        return answer;
    }
}
