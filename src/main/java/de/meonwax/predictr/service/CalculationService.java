package de.meonwax.predictr.service;

import de.meonwax.predictr.domain.Answer;
import de.meonwax.predictr.domain.Bet;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.repository.AnswerRepository;
import de.meonwax.predictr.repository.BetRepository;
import de.meonwax.predictr.settings.Settings;
import de.meonwax.predictr.util.Utils;
import lombok.AllArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.ZonedDateTime;
import java.util.List;

@Service
@AllArgsConstructor
public class CalculationService {

    private final Settings settings;

    private final BetRepository betRepository;

    private final AnswerRepository answerRepository;

    int getPoints(User user) {

        int points = 0;

        List<Bet> bets = betRepository.findByUserAndGameKickoffTimeBefore(user, ZonedDateTime.now());
        for (Bet bet : bets) {
            points += calculate(bet);
        }

        List<Answer> answers = answerRepository.findByUserAndQuestionDeadlineBefore(user, ZonedDateTime.now());
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

        // TODO: Implement this check in a JPA custom query
        if (Utils.allNotNull(betScoreHome, betScoreAway, resultScoreHome, resultScoreAway)) {

            if (betScoreHome.equals(resultScoreHome) && betScoreAway.equals(resultScoreAway)) {
                return settings.getPoints().getResult();
            }

            int betSpread = betScoreHome - betScoreAway;
            int resultSpread = resultScoreHome - resultScoreAway;
            if (betSpread == resultSpread) {
                return settings.getPoints().getTendencySpread();
            }

            if (betSpread * resultSpread > 0) {
                return settings.getPoints().getTendency();
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
        if (Utils.allNotNull(userAnswer, correctAnswer)) {
            for (String s : correctAnswer.split(",")) {
                if (userAnswer.toLowerCase().trim().contains(s.trim().toLowerCase())) {
                    return answer.getQuestion().getPoints();
                }
            }
        }
        return 0;
    }

    String getCssClass(Bet bet) {
        int points = calculate(bet);
        if (points == settings.getPoints().getResult()) {
            return "success bold";
        }
        if (points == settings.getPoints().getTendencySpread()) {
            return "info";
        }
        if (points == settings.getPoints().getTendency()) {
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
