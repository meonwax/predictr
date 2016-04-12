package de.meonwax.predictr.service;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.dto.Rank;
import de.meonwax.predictr.repository.UserRepository;
import de.meonwax.predictr.util.SortedContainer;

@Service
public class LadderService {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private CalculationService calculateService;

    public List<Rank> getLadder(boolean jackpotOnly) {
        SortedContainer<Integer, User> sortedUsers = getSortedUsers(jackpotOnly);
        return createLadder(sortedUsers);
    }

    private SortedContainer<Integer, User> getSortedUsers(boolean jackpotOnly) {
        List<User> users = jackpotOnly ? userRepository.findByWagerGreaterThan(BigDecimal.ZERO) : userRepository.findAll();
        SortedContainer<Integer, User> sortedUsers = new SortedContainer<>();
        for (User user : users) {
            sortedUsers.put(calculateService.getPoints(user), user);
        }
        return sortedUsers;
    }

    private List<Rank> createLadder(SortedContainer<Integer, User> sortedUsers) {

        List<Rank> ladder = new ArrayList<Rank>();

        // Sort entries descending
        List<SortedContainer<Integer, User>.Entry> entryList = sortedUsers.entryList();
        Collections.reverse(entryList);

        int previousPoints = 0;
        int position = 1;

        for (SortedContainer<Integer, User>.Entry e : entryList) {
            int points = e.getKey();
            ladder.add(new Rank(e.getValue(), points, previousPoints != points ? position : null));
            previousPoints = points;
            position++;
        }
        return ladder;
    }
}
