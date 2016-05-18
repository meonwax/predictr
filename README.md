# Predictr

A football prediction game.  
Data for UEFA EURO 2016 included.

## Development

* Run with development profile:

    vn spring-boot:run

* Open [http://localhost:8081](http://localhost:8081) in a web browser.

## Production

* Build the production jar using Maven:

    mvn clean package

* For database tasks, i recommend using a database manipulating tool like [Adminer](https://www.adminer.org) or [phpMyAdmin](https://www.phpmyadmin.net).

* Create a MySQL database and grant access rights to a user.

* Run with production profile:

    java -jar target/predictr*.jar --spring.profiles.active=production --spring.datasource.url=jdbc:mysql://dbhost/dbname --spring.datasource.username=dbuser --spring.datasource.password=dbpassword

* Open [http://localhost:8080/#/register](http://localhost:8080/#/register) in a web browser and register a new user.

* Upgrade the created user to an admin setting the field `role` to `ROLE_ADMIN`.

* You can now [log in](http://localhost:8080/#/login) using the admin user.
