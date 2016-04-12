package de.meonwax.predictr.web;

import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import de.meonwax.predictr.dto.Rank;
import de.meonwax.predictr.service.LadderService;

@RestController
@RequestMapping("api")
public class LadderController {

    private final Logger log = LoggerFactory.getLogger(LadderController.class);

    @Autowired
    private LadderService ladderService;

    @RequestMapping(value = "/ladder", method = RequestMethod.GET, produces = MediaType.APPLICATION_JSON_VALUE)
    public List<Rank> getAll(@RequestParam(value = "jackpot_only", required = false, defaultValue = "0") Boolean jackpotOnly) {
        return ladderService.getLadder(jackpotOnly);
    }
}
