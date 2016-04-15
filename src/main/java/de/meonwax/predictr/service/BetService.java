package de.meonwax.predictr.service;

import java.util.ArrayList;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import de.meonwax.predictr.domain.Bet;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.dto.BetDto;
import de.meonwax.predictr.repository.BetRepository;

@Service
public class BetService {

    private final Logger log = LoggerFactory.getLogger(BetService.class);

    @Autowired
    private BetRepository betRepository;

    public void update(User user, List<BetDto> betDtos) {
        List<Bet> bets = new ArrayList<>();
        for (BetDto betDto : betDtos) {
            Bet bet = betRepository.findOneByUserAndGame(user, betDto.getGame());
            if (bet == null) {
                bet = new Bet();
            }
            BeanUtils.copyProperties(betDto, bet);
            bet.setUser(user);
            bets.add(bet);
        }
        betRepository.save(bets);
    }

}
