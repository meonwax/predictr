package de.meonwax.predictr.web;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

import de.meonwax.predictr.domain.Question;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.repository.QuestionRepository;

@RestController
@RequestMapping("api")
public class QuestionController {

    @Autowired
    private QuestionRepository questionRepository;

    @RequestMapping(value = "/questions", method = RequestMethod.GET, produces = MediaType.APPLICATION_JSON_VALUE)
    public List<Question> getAll(@AuthenticationPrincipal User user) {
        return questionRepository.findAllWithUsersAnswers(user);
    }
}
