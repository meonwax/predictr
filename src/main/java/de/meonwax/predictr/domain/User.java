package de.meonwax.predictr.domain;

import java.io.Serializable;
import java.math.BigDecimal;
import java.time.ZonedDateTime;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Set;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.EntityListeners;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import javax.persistence.OneToMany;
import javax.validation.constraints.Min;
import javax.validation.constraints.NotNull;

import org.hibernate.validator.constraints.Email;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

import com.fasterxml.jackson.annotation.JsonIgnore;

@Entity
@EntityListeners(AuditingEntityListener.class)
public class User implements Serializable, UserDetails {

    private static final long serialVersionUID = 1L;

    public final static String ROLE_ADMIN = "ROLE_ADMIN";
    public final static String ROLE_USER = "ROLE_USER";

    @Id
    @GeneratedValue
    private Long id;

    @CreatedDate
    @NotNull
    private ZonedDateTime createdDate = ZonedDateTime.now();

    @LastModifiedDate
    @NotNull
    private ZonedDateTime lastModifiedDate = ZonedDateTime.now();

    @NotNull
    @Email
    @Column(unique = true, nullable = false)
    private String email;

    @NotNull
    @Column(nullable = false)
    @JsonIgnore
    private String password;

    @NotNull
    @Column(nullable = false)
    private String name;

    @NotNull
    @Column(nullable = false)
    private String role;

    @NotNull
    @Min(value = 0)
    @Column(nullable = false)
    private BigDecimal wager;

    @OneToMany(mappedBy = "user")
    @JsonIgnore
    private Set<Shout> shouts;

    @OneToMany(mappedBy = "user")
    private Set<Bet> bets;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public ZonedDateTime getCreatedDate() {
        return createdDate;
    }

    public void setCreatedDate(ZonedDateTime createdDate) {
        this.createdDate = createdDate;
    }

    public ZonedDateTime getLastModifiedDate() {
        return lastModifiedDate;
    }

    public void setLastModifiedDate(ZonedDateTime lastModifiedDate) {
        this.lastModifiedDate = lastModifiedDate;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    @Override
    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getRole() {
        return role;
    }

    public void setRole(String role) {
        this.role = role;
    }

    public BigDecimal getWager() {
        return wager;
    }

    public void setWager(BigDecimal wager) {
        this.wager = wager;
    }

    public Set<Shout> getShouts() {
        return shouts;
    }

    public void setShouts(Set<Shout> shouts) {
        this.shouts = shouts;
    }

    public Set<Bet> getBets() {
        return bets;
    }

    public void setBets(Set<Bet> bets) {
        this.bets = bets;
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
}