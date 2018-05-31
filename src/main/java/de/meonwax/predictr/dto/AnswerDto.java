package de.meonwax.predictr.dto;

import de.meonwax.predictr.domain.Question;
import de.meonwax.predictr.domain.User;
import lombok.Data;

import javax.validation.constraints.NotNull;

@Data
public class AnswerDto {

    @NotNull
    private Question question;

    @NotNull
    private String answer;

    private User user;

    private String cssClass;
}
