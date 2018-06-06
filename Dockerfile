FROM openjdk:10.0.1-jdk-slim
VOLUME /tmp
ARG JAR_FILE
ADD /target/${JAR_FILE} app.jar
ENTRYPOINT ["java", "-Djava.security.egd=file:/dev/./urandom", "-jar", "/app.jar"]
