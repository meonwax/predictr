package de.meonwax.predictr.domain;

import lombok.Data;

import javax.persistence.*;
import javax.validation.constraints.NotNull;
import java.time.Instant;
import java.util.Set;

@Entity
@Data
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

    // Artificial value for displaying only the first element in the client
    public String getCorrectAnswerSimplified() {
        return correctAnswer != null ? correctAnswer.split(",")[0] : null;
    }
}
