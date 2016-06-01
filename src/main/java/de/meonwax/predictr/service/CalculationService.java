package de.meonwax.predictr.service;

import java.time.ZonedDateTime;
import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import de.meonwax.predictr.domain.Answer;
import de.meonwax.predictr.domain.Bet;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.repository.AnswerRepository;
import de.meonwax.predictr.repository.BetRepository;
import de.meonwax.predictr.util.Utils;

@Service
public class CalculationService {

    @Value("${predictr.points.result}")
    private Integer pointsResult;

    @Value("${predictr.points.tendency}")
    private Integer pointsTendency;

    @Value("${predictr.points.tendencySpread}")
    private Integer pointsTendencySpread;

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
    public int calculate(Bet bet) {

        Integer betScoreHome = bet.getScoreHome();
        Integer betScoreAway = bet.getScoreAway();

        Integer resultScoreHome = bet.getGame().getScoreHome();
        Integer resultScoreAway = bet.getGame().getScoreAway();

        // TODO: Implement this check in a JPA custom query
        if (Utils.allNotNull(betScoreHome, betScoreAway, resultScoreHome, resultScoreAway)) {

            if (betScoreHome.equals(resultScoreHome) && betScoreAway.equals(resultScoreAway)) {
                return pointsResult;
            }

            int betSpread = betScoreHome - betScoreAway;
            int resultSpread = resultScoreHome - resultScoreAway;
            if (betSpread == resultSpread) {
                return pointsTendencySpread;
            }

            if (betSpread * resultSpread > 0) {
                return pointsTendency;
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

        // TODO: Implement this check in a JPA custom query
        if (Utils.allNotNull(userAnswer, correctAnswer)) {
            if (userAnswer.toLowerCase().trim().equals(correctAnswer.toLowerCase())) {
                return answer.getQuestion().getPoints();
            }
        }
        return 0;
    }
}
