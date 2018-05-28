package de.meonwax.predictr.service;

import de.meonwax.predictr.domain.Bet;
import de.meonwax.predictr.domain.Game;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.dto.BetDto;
import de.meonwax.predictr.repository.BetRepository;
import de.meonwax.predictr.repository.GameRepository;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.ZonedDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

@Service
public class BetService {

    @Autowired
    private BetRepository betRepository;

    @Autowired
    private GameRepository gameRepository;

    @Autowired
    private CalculationService calculationService;

    public void update(User user, List<BetDto> betDtos) {
        List<Bet> bets = new ArrayList<>();
        for (BetDto betDto : betDtos) {
            Optional<Game> game = gameRepository.findById(betDto.getGame().getId());
            if (game.isPresent()) {
                // Prevent saving if game has already started
                if (game.get().getKickoffTime().isAfter(ZonedDateTime.now())) {
                    Bet bet = betRepository.findOneByUserAndGame(user, game.get());
                    if (bet == null) {
                        bet = new Bet();
                    }
                    BeanUtils.copyProperties(betDto, bet);
                    bet.setUser(user);
                    bets.add(bet);
                }
            }
        }
        betRepository.saveAll(bets);
    }

    public Optional<List<BetDto>> getOther(User ownUser, Long gameId) {

        Optional<Game> game = gameRepository.findById(gameId);

        // Only return data if game has already started
        if (!game.isPresent() || game.get().getKickoffTime().isAfter(ZonedDateTime.now())) {
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
