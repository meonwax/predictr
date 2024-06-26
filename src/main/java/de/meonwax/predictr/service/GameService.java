package de.meonwax.predictr.service;

import de.meonwax.predictr.domain.Bet;
import de.meonwax.predictr.domain.Game;
import de.meonwax.predictr.domain.Group;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.dto.GameDto;
import de.meonwax.predictr.repository.GameRepository;
import de.meonwax.predictr.repository.GroupRepository;
import lombok.AllArgsConstructor;
import org.springframework.beans.BeanUtils;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;

import java.time.Clock;
import java.time.Instant;
import java.util.*;

@Service
@AllArgsConstructor
public class GameService {

    private final GameRepository gameRepository;

    private final GroupRepository groupRepository;

    private final CalculationService calculationService;

    private final Clock clock;

    public List<Game> getAll() {
        return gameRepository.findAll();
    }

    public void update(List<GameDto> gameDtos) {
        List<Game> games = new ArrayList<>();
        for (GameDto gameDto : gameDtos) {
            Game game = gameRepository
                .findById(gameDto.getId())
                .orElseGet(Game::new);
            BeanUtils.copyProperties(gameDto, game);
            games.add(game);
        }
        gameRepository.saveAll(games);
    }

    public List<Game> getUpcoming() {
        return gameRepository.findByKickoffTimeAfterOrderByKickoffTime(PageRequest.of(0, 5), Instant.now(clock));
    }

    public List<Game> getRunning() {
        return gameRepository.findByKickoffTimeBeforeAndScoreHomeIsNullAndScoreAwayIsNullOrderByKickoffTime(Instant.now(clock));
    }

    public Map<String, Long> getProgress() {
        long gamesCount = gameRepository.count();
        long gamesFinished = gameRepository.countByScoreHomeIsNotNullAndScoreAwayIsNotNull();
        Map<String, Long> result = new HashMap<>();
        result.put("amount", gamesCount);
        result.put("finished", gamesFinished);
        return result;
    }

    public List<Group> getAllGroupsWithUsersBets(User user) {
        List<Group> groups = groupRepository.findAllWithGames();
        for (Group group : groups) {
            for (Game game : group.getGames()) {
                if (!game.getBets().isEmpty()) {

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
                        game.setPointsEarned(calculationService.calculate(usersBet));
                        // Set only user's bet to result
                        game.setBets(new HashSet<>(Collections.singletonList(usersBet)));
                    } else {
                        // Delete all bets from result
                        game.setBets(new HashSet<>());
                    }
                }
            }
        }
        return groups;
    }
}
