package de.meonwax.predictr.service;

import java.time.ZonedDateTime;
import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import de.meonwax.predictr.domain.Answer;
import de.meonwax.predictr.domain.Bet;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.repository.AnswerRepository;
import de.meonwax.predictr.repository.BetRepository;
import de.meonwax.predictr.settings.Settings;
import de.meonwax.predictr.util.Utils;

@Service
public class CalculationService {

    @Autowired
    private Settings settings;

    @Autowired
    private BetRepository betRepository;

    @Autowired
    private AnswerRepository answerRepository;

    public int getPoints(User user) {

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
     * Calculate points for a special question/answer
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

    public String getCssClass(Bet bet) {
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

    public String getCssClass(Answer answer) {
        int points = calculate(answer);
        if (points == answer.getQuestion().getPoints()) {
            return "success bold";
        }
        return null;
    }
}
