package de.meonwax.predictr.domain;

import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Data;

import javax.persistence.*;

@Data
@Entity
public class Avatar {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Lob
    @Column(length = 100000)
    @JsonIgnore
    private byte[] data;

    @Column(nullable = false)
    private String mimeType;

    @OneToOne(mappedBy = "avatar")
    @JsonIgnore
    private User user;
}
