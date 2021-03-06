package de.meonwax.predictr.service;

import de.meonwax.predictr.domain.Bet;
import de.meonwax.predictr.domain.Game;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.dto.BetDto;
import de.meonwax.predictr.repository.BetRepository;
import de.meonwax.predictr.repository.GameRepository;
import lombok.AllArgsConstructor;
import org.springframework.beans.BeanUtils;
import org.springframework.stereotype.Service;

import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

@Service
@AllArgsConstructor
public class BetService {

    private final BetRepository betRepository;

    private final GameRepository gameRepository;

    private final CalculationService calculationService;

    private final Clock clock;

    public void update(User user, List<BetDto> betDtos) {
        List<Bet> bets = new ArrayList<>();
        for (BetDto betDto : betDtos) {
            gameRepository.findById(betDto.getGame().getId())
                .ifPresent(game -> {
                    // Prevent saving if game has already started
                    if (game.getKickoffTime().isAfter(Instant.now(clock))) {
                        Bet bet = betRepository
                            .findOneByUserAndGame(user, game)
                            .orElse(new Bet());
                        BeanUtils.copyProperties(betDto, bet);
                        bet.setUser(user);
                        bets.add(bet);
                    }
                });
        }
        betRepository.saveAll(bets);
    }

    public Optional<List<BetDto>> getOther(User ownUser, Long gameId) {

        Optional<Game> game = gameRepository.findById(gameId);

        // Only return data if game has already started
        if (!game.isPresent() || game.get().getKickoffTime().isAfter(Instant.now(clock))) {
            return Optional.empty();
        }

        // Build the result
        List<BetDto> result = new ArrayList<>();
        for (Bet bet : game.get().getBets()) {
            // Filter out own user
            if (!bet.getUser().equals(ownUser)) {
                BetDto dto = new BetDto();
                dto.setUser(bet.getUser());
                dto.setScoreHome(bet.getScoreHome());
                dto.setScoreAway(bet.getScoreAway());
                dto.setCssClass(calculationService.getCssClass(bet));
                result.add(dto);
            }
        }
        return Optional.of(result);
    }
}
