package de.meonwax.service;

import java.time.ZonedDateTime;
import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.env.Environment;
import org.springframework.stereotype.Service;

import de.meonwax.domain.Answer;
import de.meonwax.domain.Bet;
import de.meonwax.domain.User;
import de.meonwax.repository.AnswerRepository;
import de.meonwax.repository.BetRepository;
import de.meonwax.util.Utils;

@Service
public class CalculationService {

    @Autowired
    private Environment env;

    @Autowired
    private BetRepository betRepository;

    @Autowired
    private AnswerRepository answerRepository;

    public int getPoints(User user) {

//        if (true) {
//            return new Random().nextInt(10);
//        }

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
    private int calculate(Bet bet) {

        Integer betScoreHome = bet.getScoreHome();
        Integer betScoreAway = bet.getScoreAway();

        Integer resultScoreHome = bet.getGame().getScoreHome();
        Integer resultScoreAway = bet.getGame().getScoreAway();

        // TODO: Implement this check in a JPA custom query
        if (Utils.allNotNull(betScoreHome, betScoreAway, resultScoreHome, resultScoreAway)) {

            if (betScoreHome.equals(resultScoreHome) && betScoreAway.equals(resultScoreAway)) {
                return env.getProperty("points.result", Integer.class, 0);
            }

            int betSpread = betScoreHome - betScoreAway;
            int resultSpread = resultScoreHome - resultScoreAway;
            if (betSpread == resultSpread) {
                return env.getProperty("points.tendencySpread", Integer.class, 0);
            }

            if (betSpread * resultSpread > 0) {
                return env.getProperty("points.tendency", Integer.class, 0);
            }
        }
        return 0;
    }

    /**
     * Calculate points for a special question/answer
     */
    private int calculate(Answer answer) {

        String userAnswer = answer.getAnswer();
        String correctAnswer = answer.getQuestion().getCorrectAnswer();

        // TODO: Implement this check in a JPA custom query
        if (Utils.allNotNull(userAnswer, correctAnswer)) {
            if (userAnswer.toLowerCase().trim().equals(correctAnswer.toLowerCase())) {
                return answer.getQuestion().getPoints();
            }
        }
        return 0;
    }
}
