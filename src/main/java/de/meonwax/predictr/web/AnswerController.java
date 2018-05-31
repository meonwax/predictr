package de.meonwax.predictr.web;

import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.dto.AnswerDto;
import de.meonwax.predictr.service.AnswerService;
import lombok.AllArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.List;

@RestController
@RequestMapping("api")
@AllArgsConstructor
public class AnswerController {

    private final AnswerService answerService;

    @RequestMapping(value = "/answers", method = RequestMethod.POST, produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Void> bet(@Valid @RequestBody List<AnswerDto> answerDtos, @AuthenticationPrincipal User user) {
        if (answerDtos.isEmpty()) {
            return ResponseEntity.badRequest().build();
        }
        answerService.update(user, answerDtos);
        return ResponseEntity.noContent().build();
    }

    /**
     * Retrieve the answers of other users for specific question
     */
    @RequestMapping(value = "/answers/{questionId}", method = RequestMethod.GET, produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<List<AnswerDto>> getOther(@PathVariable Long questionId, @AuthenticationPrincipal User user) {
        return answerService.getOther(user, questionId)
            .map(answers -> new ResponseEntity<>(answers, HttpStatus.OK))
            .orElse(new ResponseEntity<>(HttpStatus.LOCKED));
    }
}
