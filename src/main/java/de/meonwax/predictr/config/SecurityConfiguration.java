package de.meonwax.predictr.config;

import de.meonwax.predictr.security.RestAuthenticationEntryPoint;
import de.meonwax.predictr.security.RestAuthenticationFailureHandler;
import de.meonwax.predictr.security.RestAuthenticationSuccessHandler;
import de.meonwax.predictr.security.RestLogoutSuccessHandler;
import de.meonwax.predictr.service.UserService;
import lombok.AllArgsConstructor;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.authentication.builders.AuthenticationManagerBuilder;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.crypto.password.PasswordEncoder;

@Configuration
@EnableGlobalMethodSecurity(securedEnabled = true)
//@Order(SecurityProperties.ACCESS_OVERRIDE_ORDER)
@AllArgsConstructor
public class SecurityConfiguration extends WebSecurityConfigurerAdapter {

    private final RestAuthenticationEntryPoint authenticationEntryPoint;

    private final RestAuthenticationSuccessHandler authenticationSuccessHandler;

    private final RestAuthenticationFailureHandler authenticationFailureHandler;

    private final RestLogoutSuccessHandler logoutSuccessHandler;

    private final UserService userService;

    private final PasswordEncoder passwordEncoder;

//    private final RememberMeServices rememberMeServices;

//    private final Settings settings;

    public void configureGlobal(AuthenticationManagerBuilder auth) throws Exception {
        auth.userDetailsService(userService).passwordEncoder(passwordEncoder);
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
            .deleteCookies("JSESSIONID");

//            .and().rememberMe()
//            .rememberMeServices(rememberMeServices)
//            .rememberMeParameter("remember-me")
//            .key(settings.getRememberMeKey());
    }
}
