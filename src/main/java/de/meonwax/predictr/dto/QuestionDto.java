package de.meonwax.predictr.dto;

import java.time.ZonedDateTime;

import javax.validation.constraints.NotNull;

import de.meonwax.predictr.util.Utils;

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

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getQuestion() {
        return question;
    }

    public void setQuestion(String question) {
        this.question = question;
    }

    public ZonedDateTime getDeadline() {
        return deadline;
    }

    public void setDeadline(ZonedDateTime deadline) {
        this.deadline = deadline;
    }

    public Integer getPoints() {
        return points;
    }

    public void setPoints(Integer points) {
        this.points = points;
    }

    public String getCorrectAnswer() {
        return correctAnswer;
    }

    public void setCorrectAnswer(String correctAnswer) {
        this.correctAnswer = correctAnswer;
    }

    @Override
    public String toString() {
        return Utils.jsonSerialize(this, true);
    }
}
