package de.meonwax.predictr.config;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.security.SecurityProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.annotation.Order;
import org.springframework.security.config.annotation.authentication.builders.AuthenticationManagerBuilder;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.rememberme.PersistentTokenRepository;

import de.meonwax.predictr.security.RestAuthenticationEntryPoint;
import de.meonwax.predictr.security.RestAuthenticationFailureHandler;
import de.meonwax.predictr.security.RestAuthenticationSuccessHandler;
import de.meonwax.predictr.security.RestLogoutSuccessHandler;
import de.meonwax.predictr.service.UserService;
import de.meonwax.predictr.settings.Settings;

@Configuration
@EnableGlobalMethodSecurity(securedEnabled = true)
@Order(SecurityProperties.ACCESS_OVERRIDE_ORDER)
public class SecurityConfiguration extends WebSecurityConfigurerAdapter {

    @Autowired
    private UserService userService;

    @Autowired
    private RestAuthenticationEntryPoint authenticationEntryPoint;

    @Autowired
    private RestAuthenticationSuccessHandler authenticationSuccessHandler;

    @Autowired
    private RestAuthenticationFailureHandler authenticationFailureHandler;

    @Autowired
    private RestLogoutSuccessHandler logoutSuccessHandler;

    @Autowired
    private PersistentTokenRepository tokenRepository;

    @Autowired
    private Settings settings;

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Autowired
    public void configureGlobal(AuthenticationManagerBuilder auth) throws Exception {
        auth.userDetailsService(userService).passwordEncoder(passwordEncoder());
    }

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
                //.and().addFilterAfter(new CsrfHeaderFilter(), CsrfFilter.class);

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
                .key(settings.getRememberMeKey())
                .tokenRepository(tokenRepository);
    }
}
