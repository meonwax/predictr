package de.meonwax.predictr.web;

import de.meonwax.predictr.dto.RankDto;
import de.meonwax.predictr.repository.UserRepository;
import de.meonwax.predictr.service.LadderService;
import lombok.AllArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.math.BigDecimal;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("api")
@AllArgsConstructor
public class LadderController {

    private final LadderService ladderService;

    private final UserRepository userRepository;

    @RequestMapping(value = "/ladder", method = RequestMethod.GET, produces = MediaType.APPLICATION_JSON_VALUE)
    public List<RankDto> getAll(@RequestParam(value = "jackpot_only", required = false, defaultValue = "0") Boolean jackpotOnly) {
        return ladderService.getLadder(jackpotOnly);
    }

    @RequestMapping(value = "/ladder/jackpot", method = RequestMethod.GET, produces = MediaType.APPLICATION_JSON_VALUE)
    public Map<String, BigDecimal> getFullJackpot() {
        Map<String, BigDecimal> result = new HashMap<>();
        result.put("value", userRepository.getFullJackpot());
        return result;
    }
}
