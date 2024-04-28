package de.meonwax.predictr.domain;

import lombok.Data;

import javax.persistence.*;
import java.time.ZonedDateTime;
import java.util.UUID;

@Data
@Entity
public class PasswordResetToken {

    private static final int EXPIRATION_IN_MINUTES = 60 * 24;

    public PasswordResetToken() {
    }

    public PasswordResetToken(User user) {
        this.user = user;
        this.value = UUID.randomUUID().toString().replaceAll("-", "");
        this.expiry = ZonedDateTime.now().plusMinutes(EXPIRATION_IN_MINUTES);
    }

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "val", unique = true, nullable = false)
    private String value;

    @Column(nullable = false)
    private ZonedDateTime expiry;

    @OneToOne(optional = false)
    private User user;
}
