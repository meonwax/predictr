package de.meonwax.predictr.service;

import java.time.ZonedDateTime;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;

import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;

import de.meonwax.predictr.domain.Bet;
import de.meonwax.predictr.domain.Game;
import de.meonwax.predictr.domain.Group;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.dto.GameDto;
import de.meonwax.predictr.repository.GameRepository;
import de.meonwax.predictr.repository.GroupRepository;

@Service
public class GameService {

    @Autowired
    private GameRepository gameRepository;

    @Autowired
    private GroupRepository groupRepository;

    @Autowired
    private CalculationService calculationService;

    public List<Game> getAll() {
        return gameRepository.findAll();
    }

    public void update(List<GameDto> gameDtos) {
        List<Game> games = new ArrayList<>();
        for (GameDto gameDto : gameDtos) {
            Game game = gameRepository.findOne(gameDto.getId());
            if (game == null) {
                game = new Game();
            }
            BeanUtils.copyProperties(gameDto, game);
            games.add(game);
        }
        gameRepository.save(games);
    }

    public List<Game> getUpcoming() {
        return gameRepository.findByKickoffTimeAfterOrderByKickoffTime(new PageRequest(0, 5), ZonedDateTime.now());
    }

    public List<Game> getRunning() {
        return gameRepository.findByKickoffTimeBeforeAndScoreHomeIsNullAndScoreAwayIsNullOrderByKickoffTime(ZonedDateTime.now());
    }

    public List<Group> findAllGroupsWithUsersBets(User user) {
        List<Group> groups = groupRepository.findAllWithGames();
        for (Group group : groups) {
            for (Game game : group.getGames()) {
                if (game.getBets().size() > 0) {

                    // Fetch user's bet
                    Bet usersBet = null;
                    for (Bet bet : game.getBets()) {
                        if (bet.getUser().equals(user)) {
                            usersBet = bet;
                            break;
                        }
                    }

                    if (usersBet != null) {
                        // Calculate points
                        game.setPointsEarned(calculationService.calculate(game.getBets().iterator().next()));
                        // Set only user's bet to result
                        game.setBets(new HashSet<Bet>(Arrays.asList(usersBet)));
                    } else {
                        // Delete all bets from result
                        game.setBets(new HashSet<Bet>());
                    }
                }
            }
        }
        return groups;
    }
}
