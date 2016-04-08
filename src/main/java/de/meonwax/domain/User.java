package de.meonwax.domain;

import java.io.Serializable;
import java.math.BigDecimal;
import java.time.ZonedDateTime;
import java.util.Set;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.EntityListeners;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import javax.persistence.OneToMany;
import javax.validation.constraints.Min;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Size;

import org.hibernate.validator.constraints.Email;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import com.fasterxml.jackson.annotation.JsonIgnore;

@Entity
@EntityListeners(AuditingEntityListener.class)
public class User implements Serializable {

    private static final long serialVersionUID = 1L;

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
    @Size(max = 255)
    @Column(length = 255, unique = true, nullable = false)
    private String email;

    @NotNull
    @Size(min = 5, max = 100)
    @Column(length = 100)
    @JsonIgnore
    private String password;

    private String name;

    @NotNull
    @Column(nullable = false)
    private Boolean isAdmin;

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

    public Boolean getIsAdmin() {
        return isAdmin;
    }

    public void setIsAdmin(Boolean isAdmin) {
        this.isAdmin = isAdmin;
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
}
