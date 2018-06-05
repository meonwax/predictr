package de.meonwax.predictr.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonProperty.Access;
import lombok.Getter;
import lombok.Setter;

import javax.validation.constraints.Email;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Size;

@Getter
@Setter
public class UserDto {

    @NotNull
    @Email
    @Size(max = 255)
    private String email;

    @NotNull
    @Size(min = 5, max = 100)
    @JsonProperty(access = Access.WRITE_ONLY)
    private String password;

    @NotNull
    @Size(max = 255)
    private String name;

    @Override
    public String toString() {
        return "UserDto{" +
            "email='" + email + '\'' +
            ", name='" + name + '\'' +
            '}';
    }
}
