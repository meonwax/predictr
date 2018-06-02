package de.meonwax.predictr.domain;

import javax.persistence.*;
import javax.validation.constraints.NotNull;
import java.time.Instant;
import java.util.Set;

@Entity
public class Question {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @NotNull
    @Column(nullable = false)
    private String question;
    @NotNull
    @Column(nullable = false)
    private Instant deadline;

    @NotNull
    @Column(nullable = false)
    private Integer points;

    @Transient
    private Integer pointsEarned;

    private String correctAnswer;

    @OneToMany(mappedBy = "question")
    private Set<Answer> answers;

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

    public Instant getDeadline() {
        return deadline;
    }

    public void setDeadline(Instant date) {
        this.deadline = date;
    }

    public Integer getPoints() {
        return points;
    }

    public void setPoints(Integer points) {
        this.points = points;
    }

    public Integer getPointsEarned() {
        return pointsEarned;
    }

    public void setPointsEarned(Integer pointsEarned) {
        this.pointsEarned = pointsEarned;
    }

    public String getCorrectAnswer() {
        return correctAnswer;
    }

    public void setCorrectAnswer(String correctAnswer) {
        this.correctAnswer = correctAnswer;
    }

    public Set<Answer> getAnswers() {
        return answers;
    }

    public void setAnswers(Set<Answer> answers) {
        this.answers = answers;
    }

    // Artificial value for displaying only the first element in the client
    public String getCorrectAnswerSimplified() {
        return correctAnswer != null ? correctAnswer.split(",")[0] : null;
    }
}
