FROM eclipse-temurin:8-jre-jammy
ADD target/predictr-*.jar app.jar
ENTRYPOINT ["java", "-Xms128m", "-Xmx1024m", "-jar", "/app.jar"]
