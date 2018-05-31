package de.meonwax.predictr.domain;

import javax.persistence.*;
import java.time.ZonedDateTime;
import java.util.UUID;

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

    @Column(unique = true, nullable = false)
    private String value;

    @Column(nullable = false)
    private ZonedDateTime expiry;

    @OneToOne(optional = false)
    private User user;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getValue() {
        return value;
    }

    public void setValue(String value) {
        this.value = value;
    }

    public ZonedDateTime getExpiry() {
        return expiry;
    }

    public void setExpiry(ZonedDateTime expiry) {
        this.expiry = expiry;
    }

    public User getUser() {
        return user;
    }

    public void setUser(User user) {
        this.user = user;
    }
}
