FROM openjdk:10.0.1-jdk-slim
RUN apt-get update && apt-get install -y libtcnative-1 && rm -rf /var/lib/apt/lists/*
VOLUME /tmp
ARG JAR_FILE
ADD /target/${JAR_FILE} app.jar
ENTRYPOINT ["java", "-Djava.security.egd=file:/dev/./urandom", "-jar", "/app.jar"]
