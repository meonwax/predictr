package de.meonwax.predictr.dto;

import lombok.Data;

import javax.validation.constraints.NotNull;
import java.time.ZonedDateTime;

@Data
public class QuestionDto {

    @NotNull
    private Long id;

    @NotNull
    private String question;

    @NotNull
    private ZonedDateTime deadline;

    @NotNull
    private Integer points;

    private String correctAnswer;
}
