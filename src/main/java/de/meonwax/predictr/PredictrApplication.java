package de.meonwax.predictr;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

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
}
