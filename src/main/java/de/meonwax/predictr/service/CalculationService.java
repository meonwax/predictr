package de.meonwax.predictr.service;

import de.meonwax.predictr.domain.Answer;
import de.meonwax.predictr.domain.Bet;
import de.meonwax.predictr.domain.Config;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.repository.AnswerRepository;
import de.meonwax.predictr.repository.BetRepository;
import lombok.AllArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.stream.Stream;

@Service
@AllArgsConstructor
public class CalculationService {

    private final ConfigService configService;

    private final BetRepository betRepository;

    private final AnswerRepository answerRepository;

    private final Clock clock;

    int getPoints(User user) {

        int points = 0;

        List<Bet> bets = betRepository.findByUserAndGameKickoffTimeBefore(user, Instant.now(clock));
        for (Bet bet : bets) {
            points += calculate(bet);
        }

        List<Answer> answers = answerRepository.findByUserAndQuestionDeadlineBefore(user, Instant.now(clock));
        for (Answer answer : answers) {
            points += calculate(answer);
        }

        return points;
    }

    /**
     * Calculate points for a normal game bet
     */
    public int calculate(Bet bet) {

        Integer betScoreHome = bet.getScoreHome();
        Integer betScoreAway = bet.getScoreAway();

        Integer resultScoreHome = bet.getGame().getScoreHome();
        Integer resultScoreAway = bet.getGame().getScoreAway();

        if (Stream.of(betScoreHome, betScoreAway, resultScoreHome, resultScoreAway).allMatch(Objects::nonNull)) {

            Config config = configService.getConfig();

            if (betScoreHome.equals(resultScoreHome) && betScoreAway.equals(resultScoreAway)) {
                return config.getPointsResult();
            }

            int betSpread = betScoreHome - betScoreAway;
            int resultSpread = resultScoreHome - resultScoreAway;
            if (betSpread == resultSpread) {
                return config.getPointsTendencySpread();
            }

            if (betSpread * resultSpread > 0) {
                return config.getPointsTendency();
            }
        }
        return 0;
    }

    /**
     * Calculate points for a special question/answer.
     * The correct answer can be comma-separated to allow different notations and small typos.
     * Only the first element will be displayed in the client.
     */
    public int calculate(Answer answer) {
        String userAnswer = answer.getAnswer();
        String correctAnswer = answer.getQuestion().getCorrectAnswer();
        if (Stream.of(userAnswer, correctAnswer).allMatch(Objects::nonNull)) {
            for (String s : correctAnswer.split(",")) {
                if (userAnswer.toLowerCase().trim().contains(s.trim().toLowerCase())) {
                    return answer.getQuestion().getPoints();
                }
            }
        }
        return 0;
    }

    String getCssClass(Bet bet) {
        Config config = configService.getConfig();
        int points = calculate(bet);
        if (points == config.getPointsResult()) {
            return "success bold";
        }
        if (points == config.getPointsTendencySpread()) {
            return "info";
        }
        if (points == config.getPointsTendency()) {
            return "warning";
        }
        return null;
    }

    String getCssClass(Answer answer) {
        int points = calculate(answer);
        if (points == answer.getQuestion().getPoints()) {
            return "success bold";
        }
        return null;
    }
}
