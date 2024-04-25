package de.meonwax.predictr.domain;

import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Data;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

import javax.persistence.*;
import javax.validation.constraints.Email;
import javax.validation.constraints.Min;
import javax.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Set;

@Data
@Entity
@EntityListeners(AuditingEntityListener.class)
public class User implements UserDetails {

    public final static String ROLE_ADMIN = "ROLE_ADMIN";
    public final static String ROLE_USER = "ROLE_USER";

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @CreatedDate
    @NotNull
    @Column(nullable = false)
    private Instant createdDate;

    @NotNull
    @Column(nullable = false)
    private Instant lastModifiedDate;

    private Instant lastLoginDate;

    @NotNull
    @Email
    @Column(unique = true, nullable = false)
    private String email;

    @NotNull
    @Column(nullable = false)
    @JsonIgnore
    private String password;

    @OneToOne(mappedBy = "user")
    @JsonIgnore
    private PasswordResetToken passwordResetToken;

    @NotNull
    @Column(nullable = false)
    private String name;

    @NotNull
    @Column(nullable = false)
    private String role;

    @OneToOne
    @JsonIgnore
    private Avatar avatar;

    private String preferredLanguage;

    @NotNull
    @Min(value = 0)
    @Column(nullable = false)
    private BigDecimal wager;

    @OneToMany(mappedBy = "user")
    @JsonIgnore
    private Set<Shout> shouts;

    @OneToMany(mappedBy = "user")
    @JsonIgnore
    private Set<Bet> bets;

    @OneToMany(mappedBy = "user")
    @JsonIgnore
    private Set<Answer> answers;

    @Override
    public String getPassword() {
        return password;
    }

    @Override
    @JsonIgnore
    public Collection<? extends GrantedAuthority> getAuthorities() {
        Collection<GrantedAuthority> grantedAuthorities = new ArrayList<>();
        grantedAuthorities.add(new SimpleGrantedAuthority(role));
        return grantedAuthorities;
    }

    @Override
    @JsonIgnore
    public String getUsername() {
        return getEmail();
    }

    @Override
    @JsonIgnore
    public boolean isAccountNonExpired() {
        return true;
    }

    @Override
    @JsonIgnore
    public boolean isAccountNonLocked() {
        return true;
    }

    @Override
    @JsonIgnore
    public boolean isCredentialsNonExpired() {
        return true;
    }

    @Override
    @JsonIgnore
    public boolean isEnabled() {
        return true;
    }

    @Override
    public boolean equals(Object obj) {
        return obj instanceof User
            && ((User) obj).id != null
            && id != null
            && ((User) obj).id.longValue() == id.longValue();
    }

    @Override
    public int hashCode() {
        return id != null ? id.hashCode() : 0;
    }
}
