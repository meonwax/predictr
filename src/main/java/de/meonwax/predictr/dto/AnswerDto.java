package de.meonwax.predictr.dto;

import javax.validation.constraints.NotNull;

import de.meonwax.predictr.domain.Question;
import de.meonwax.predictr.util.Utils;

public class AnswerDto {

    @NotNull
    private Question question;

    @NotNull
    private String answer;

    public Question getQuestion() {
        return question;
    }

    public void setQuestion(Question question) {
        this.question = question;
    }

    public String getAnswer() {
        return answer;
    }

    public void setAnswer(String answer) {
        this.answer = answer;
    }

    @Override
    public String toString() {
        return Utils.jsonSerialize(this, true);
    }
}
