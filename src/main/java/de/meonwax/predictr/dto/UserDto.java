package de.meonwax.predictr.dto;

import javax.validation.constraints.NotNull;
import javax.validation.constraints.Size;

import org.hibernate.validator.constraints.Email;

public class UserDto {

    @NotNull
    @Email
    @Size(max = 255)
    private String email;

    @NotNull
    @Size(min = 5, max = 100)
    private String password;

    @NotNull
    @Size(max = 255)
    private String name;

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
}
