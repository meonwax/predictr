package de.meonwax.predictr.service;

import java.math.BigDecimal;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.dto.UserDto;
import de.meonwax.predictr.repository.UserRepository;

@Service
public class UserService implements UserDetailsService {

    private final Logger log = LoggerFactory.getLogger(UserService.class);

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @Override
    public UserDetails loadUserByUsername(String email) throws UsernameNotFoundException {
        if (email.length() > 0) {
            log.info("Querying user with email " + email + " from database");
            User user = userRepository.findOneByEmailIgnoringCase(email);
            if (user != null) {
                return user;
            }
            throw new UsernameNotFoundException("User with email address " + email + " not found");
        }
        throw new UsernameNotFoundException("No email address given for user query");
    }

    public User getUser(String email) {
        return userRepository.findOneByEmailIgnoringCase(email);
    }

    public List<User> getAllUsers() {
        return userRepository.findAll();
    }

    public boolean registerUser(UserDto userDto) {
        User user = new User();
        user.setName(userDto.getName());
        user.setEmail(userDto.getEmail());
        user.setPassword(passwordEncoder.encode(userDto.getPassword()));
        // Defaults for new users
        user.setRole(User.ROLE_USER);
        user.setWager(BigDecimal.valueOf(0));
        try {
            userRepository.save(user);
            return true;
        } catch (Exception e) {
            log.error("Error creating new user: " + e.getMessage());
        }
        return false;
    }

    public BigDecimal getFullJackpot() {
        return userRepository.getFullJackpot();
    }
}
