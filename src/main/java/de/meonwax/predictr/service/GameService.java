package de.meonwax.predictr.service;

import java.time.ZonedDateTime;
import java.util.ArrayList;
import java.util.List;

import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;

import de.meonwax.predictr.domain.Game;
import de.meonwax.predictr.dto.GameDto;
import de.meonwax.predictr.repository.GameRepository;

@Service
public class GameService {

    @Autowired
    private GameRepository gameRepository;

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
}
