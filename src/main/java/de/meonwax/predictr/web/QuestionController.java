package de.meonwax.predictr.web;

import java.util.List;

import javax.validation.Valid;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.annotation.Secured;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

import de.meonwax.predictr.domain.Question;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.dto.QuestionDto;
import de.meonwax.predictr.service.QuestionService;

@RestController
@RequestMapping("api")
public class QuestionController {

    @Autowired
    private QuestionService questionService;

    @RequestMapping(value = "/questions", method = RequestMethod.GET, produces = MediaType.APPLICATION_JSON_VALUE)
    public List<Question> getAll(@AuthenticationPrincipal User user) {
        return questionService.getAllWithUsersAnswers(user);
    }

    @RequestMapping(value = "/questions", method = RequestMethod.POST, produces = MediaType.APPLICATION_JSON_VALUE)
    @Secured(User.ROLE_ADMIN)
    public ResponseEntity<Void> save(@Valid @RequestBody List<QuestionDto> questionDtos) {
        if (questionDtos.isEmpty()) {
            return ResponseEntity.badRequest().build();
        }
        questionService.update(questionDtos);
        return ResponseEntity.noContent().build();
    }
}
