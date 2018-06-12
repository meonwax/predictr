package de.meonwax.predictr.config;

import de.meonwax.predictr.security.RestAuthenticationEntryPoint;
import de.meonwax.predictr.security.RestAuthenticationFailureHandler;
import de.meonwax.predictr.security.RestAuthenticationSuccessHandler;
import de.meonwax.predictr.security.RestLogoutSuccessHandler;
import de.meonwax.predictr.service.UserService;
import de.meonwax.predictr.settings.Settings;
import lombok.AllArgsConstructor;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.web.authentication.rememberme.PersistentTokenRepository;

@EnableWebSecurity
@EnableGlobalMethodSecurity(securedEnabled = true)
@AllArgsConstructor
public class SecurityConfiguration extends WebSecurityConfigurerAdapter {

    private final RestAuthenticationEntryPoint authenticationEntryPoint;

    private final RestAuthenticationSuccessHandler authenticationSuccessHandler;

    private final RestAuthenticationFailureHandler authenticationFailureHandler;

    private final RestLogoutSuccessHandler logoutSuccessHandler;

    private final PersistentTokenRepository tokenRepository;

    private final UserService userService;

    private final Settings settings;

    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http.authorizeRequests()

            .antMatchers(
                "/api/info",
                "/api/users/register",
                "/api/users/password/resetRequest",
                "/api/users/password/reset/**")
            .permitAll()

            .antMatchers("/api/**")
            .authenticated()

            .and().csrf().disable()

            .exceptionHandling().authenticationEntryPoint(authenticationEntryPoint)

            .and().headers().frameOptions().disable()

            .and().formLogin()
            .loginPage("/api/users/login")
            .successHandler(authenticationSuccessHandler)
            .failureHandler(authenticationFailureHandler)
            .usernameParameter("email")

            .and().logout()
            .logoutUrl("/api/users/logout")
            .logoutSuccessHandler(logoutSuccessHandler)
            .clearAuthentication(false)
            .deleteCookies("JSESSIONID")

            .and().rememberMe()
            .rememberMeParameter("remember-me")
            .tokenRepository(tokenRepository)
            .key(settings.getRememberMeKey())
            .userDetailsService(userService);
    }
}
