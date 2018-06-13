package de.meonwax.predictr.service;

import de.meonwax.predictr.domain.Bet;
import de.meonwax.predictr.domain.Game;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.dto.BetDto;
import de.meonwax.predictr.repository.BetRepository;
import de.meonwax.predictr.repository.GameRepository;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Captor;
import org.mockito.Mock;
import org.mockito.junit.MockitoJUnitRunner;

import java.time.Clock;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import static org.hamcrest.CoreMatchers.is;
import static org.hamcrest.MatcherAssert.assertThat;
import static org.mockito.Mockito.*;

@RunWith(MockitoJUnitRunner.class)
public class BetServiceTest {

    private BetService service;

    @Mock
    private BetRepository betRepositoryMock;

    @Mock
    private GameRepository gameRepositoryMock;

    @Mock
    private CalculationService calculationServiceMock;

    private Clock clock;

    @Captor
    private ArgumentCaptor<List<Bet>> captor;

    @Before
    public void setUp() {
        clock = Clock.systemUTC();
        service = new BetService(betRepositoryMock, gameRepositoryMock, calculationServiceMock, clock);
    }

    @Test
    public void update() {
        User user = new User();
        List<BetDto> bets = new ArrayList<>();
        bets.add(createBet(1L, Instant.now(clock).plus(1, ChronoUnit.SECONDS)));
        bets.add(createBet(2L, Instant.now(clock).plus(2, ChronoUnit.DAYS)));
        bets.add(createBet(3L, Instant.now(clock).minus(1, ChronoUnit.SECONDS)));
        bets.add(createBet(4L, Instant.now(clock).minus(3, ChronoUnit.DAYS)));
        bets.add(createBet(5L, Instant.now(clock).plus(2, ChronoUnit.HOURS)));

        service.update(user, bets);

        verify(betRepositoryMock, times(1)).saveAll(captor.capture());

        List<Bet> actual = captor.getValue();
        assertThat(actual.size(), is(3));
    }

    private BetDto createBet(Long id, Instant kickoffTime) {
        Game game = new Game();
        game.setId(id);
        game.setKickoffTime(kickoffTime);
        BetDto bet = new BetDto();
        bet.setGame(game);
        when(gameRepositoryMock.findById(id))
            .thenReturn(Optional.of(game));
        return bet;
    }
}
