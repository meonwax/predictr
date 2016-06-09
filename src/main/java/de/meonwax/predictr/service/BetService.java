package de.meonwax.predictr.service;

import java.time.ZonedDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import de.meonwax.predictr.domain.Bet;
import de.meonwax.predictr.domain.Game;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.dto.BetDto;
import de.meonwax.predictr.repository.BetRepository;
import de.meonwax.predictr.repository.GameRepository;

@Service
public class BetService {

    @Autowired
    private BetRepository betRepository;

    @Autowired
    private GameRepository gameRepository;

    public void update(User user, List<BetDto> betDtos) {
        List<Bet> bets = new ArrayList<>();
        for (BetDto betDto : betDtos) {
            Game game = gameRepository.findOne(betDto.getGame().getId());
            if (game != null) {
                // Prevent saving if game has already started
                if (game.getKickoffTime().isAfter(ZonedDateTime.now())) {
                    Bet bet = betRepository.findOneByUserAndGame(user, game);
                    if (bet == null) {
                        bet = new Bet();
                    }
                    BeanUtils.copyProperties(betDto, bet);
                    bet.setUser(user);
                    bets.add(bet);
                }
            }
        }
        betRepository.save(bets);
    }

    public Optional<List<BetDto>> getOther(User ownUser, Long gameId) {

        Game game = gameRepository.findOne(gameId);

        // Only return data if game has already started
        if (game == null || game.getKickoffTime().isAfter(ZonedDateTime.now())) {
            return Optional.empty();
        }

        // Build the result
        List<BetDto> result = new ArrayList<>();
        for (Bet bet : game.getBets()) {
            // Filter out own user
            if (!bet.getUser().equals(ownUser)) {
                BetDto dto = new BetDto();
                dto.setUser(bet.getUser());
                dto.setScoreHome(bet.getScoreHome());
                dto.setScoreAway(bet.getScoreAway());
                result.add(dto);
            }
        }
        return Optional.of(result);
    }
}
