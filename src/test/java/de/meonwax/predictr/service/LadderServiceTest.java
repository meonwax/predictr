package de.meonwax.predictr.service;

import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.dto.RankDto;
import de.meonwax.predictr.repository.UserRepository;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.Mock;
import org.mockito.junit.MockitoJUnitRunner;

import java.util.Arrays;
import java.util.List;

import static org.hamcrest.CoreMatchers.is;
import static org.hamcrest.CoreMatchers.nullValue;
import static org.hamcrest.MatcherAssert.assertThat;
import static org.mockito.Mockito.when;

@RunWith(MockitoJUnitRunner.class)
public class LadderServiceTest {

    @Mock
    private UserRepository userRepositoryMock;

    @Mock
    private CalculationService calculateServiceMock;

    private LadderService service;

    @Before
    public void setUp() {
        service = new LadderService(userRepositoryMock, calculateServiceMock);
    }

    @Test
    public void getLadder() {
        User user0 = new User();
        user0.setName("Maria");
        User user1 = new User();
        user1.setName("William");
        User user2 = new User();
        user2.setName("Jesus");
        User user3 = new User();
        user3.setName("Grace");
        List<User> users = Arrays.asList(user1, user0, user3, user2);

        when(userRepositoryMock.findAll())
            .thenReturn(users);

        when(calculateServiceMock.getPoints(user0))
            .thenReturn(5);
        when(calculateServiceMock.getPoints(user1))
            .thenReturn(1);
        when(calculateServiceMock.getPoints(user2))
            .thenReturn(7);
        when(calculateServiceMock.getPoints(user3))
            .thenReturn(5);

        List<RankDto> ladder = service.getLadder(false);

        RankDto rank = ladder.get(0);
        assertThat(rank.getUser().getName(), is("Jesus"));
        assertThat(rank.getPoints(), is(7));
        assertThat(rank.getPosition(), is(1));

        rank = ladder.get(1);
        assertThat(rank.getUser().getName(), is("Grace"));
        assertThat(rank.getPoints(), is(5));
        assertThat(rank.getPosition(), is(2));

        rank = ladder.get(2);
        assertThat(rank.getUser().getName(), is("Maria"));
        assertThat(rank.getPoints(), is(5));
        assertThat(rank.getPosition(), is(nullValue()));

        rank = ladder.get(3);
        assertThat(rank.getUser().getName(), is("William"));
        assertThat(rank.getPoints(), is(1));
        assertThat(rank.getPosition(), is(4));
    }
}
