package de.meonwax.predictr.service;

import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.dto.RankDto;
import de.meonwax.predictr.repository.UserRepository;
import de.meonwax.predictr.util.SortedContainer;
import lombok.AllArgsConstructor;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

@Service
@AllArgsConstructor
public class LadderService {

    private final UserRepository userRepository;

    private final CalculationService calculateService;

    public List<RankDto> getLadder(boolean jackpotOnly) {

        List<User> users = jackpotOnly ? userRepository.findByWagerGreaterThan(BigDecimal.ZERO) : userRepository.findAll();
        SortedContainer<Integer, User> sortedUsers = new SortedContainer<>();
        for (User user : users) {
            sortedUsers.put(calculateService.getPoints(user), user);
        }

        List<RankDto> ladder = new ArrayList<>();

        // Sort entries descending
        List<SortedContainer<Integer, User>.Entry> entryList = sortedUsers.entryList();
        Collections.reverse(entryList);

        int previousPoints = 0;
        int position = 1;

        for (SortedContainer<Integer, User>.Entry entry : entryList) {
            int points = entry.getKey();
            ladder.add(RankDto.builder()
                .user(entry.getValue())
                .points(points)
                .position(previousPoints != points ? position : null)
                .build());
            previousPoints = points;
            position++;
        }
        return ladder;
    }
}
