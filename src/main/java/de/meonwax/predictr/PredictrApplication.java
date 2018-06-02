package de.meonwax.predictr;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

import javax.annotation.PostConstruct;
import java.time.ZoneOffset;
import java.util.TimeZone;

/**
 * Don't know anymore what this was for and if we still need this
 */

//@EntityScan(basePackageClasses = {PredictrApplication.class, Jsr310JpaConverters.class})
//@SpringBootApplication
//public class PredictrApplication extends SpringBootServletInitializer {
//
//    @Override
//    protected SpringApplicationBuilder configure(SpringApplicationBuilder application) {
//        return application.sources(PredictrApplication.class);
//    }
//
//    public static void main(String[] args) {
//        SpringApplication.run(PredictrApplication.class, args);
//    }
//}

@SpringBootApplication
public class PredictrApplication {

    public static void main(String[] args) {
        SpringApplication.run(PredictrApplication.class, args);
    }

    @PostConstruct
    public void init() {
        TimeZone.setDefault(TimeZone.getTimeZone(ZoneOffset.UTC));
    }
}
