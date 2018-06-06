package de.meonwax.predictr.domain;

import lombok.Data;

import javax.persistence.*;

@Entity
@Data
public class Config {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String title;

    @Column(nullable = false)
    private String owner;

    @Column(nullable = false)
    private String adminEmail;

    @Column(nullable = false)
    private Boolean showImportantMessage;

    @Column(nullable = false)
    private Integer pointsResult;

    @Column(nullable = false)
    private Integer pointsTendency;

    @Column(nullable = false)
    private Integer pointsTendencySpread;

    @Lob
    private String rulesEn;

    @Lob
    private String rulesDe;
}
