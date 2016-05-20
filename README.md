# Predictr

A football prediction game.  
Data for UEFA EURO 2016 included.

## Requirements

* Install `jdk8`, `maven`, `ruby`, `nodejs` and `npm` using your OS package manager.

* Install the required node modules globally:

      npm install -g bower grunt-cli

* For compiling SCSS to CSS, the RubyGem `sass` is also needed:

      gem install sass


## Development

* Install the project dependencies:

      npm install
      bower install

* Run with development profile:

      mvn spring-boot:run

* Open up a new terminal and launch the node web server:

      grunt serve

* Open [http://localhost:3000](http://localhost:3000) in a web browser.

## Production

* Build the production war using Maven:

      mvn clean package

* For database tasks, i recommend using a database manipulating tool like [Adminer](https://www.adminer.org) or [phpMyAdmin](https://www.phpmyadmin.net).

* Create a MySQL database and grant access rights to a user.

* Run with production profile (replace credentials):

      java -jar target/predictr*.war \
        --spring.profiles.active=production \
        --spring.datasource.url=jdbc:mysql://dbhost/dbname \
        --spring.datasource.username=dbuser \
        --spring.datasource.password=dbpassword \
        --spring.mail.host=mailserver \
        --spring.mail.username=mailuser \
        --spring.mail.password=mailpassword
        --predictr.adminEmail=admin@example.com

* Open [http://localhost:8080/#/register](http://localhost:8080/#/register) in a web browser and register a new user.

* Upgrade the created user to an admin setting the field `role` to `ROLE_ADMIN`.

* You can now [log in](http://localhost:8080/#/login) using the admin user.
