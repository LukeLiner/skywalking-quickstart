# Build stage - skip dependency download, use pre-built jar
FROM maven:3.8-openjdk-11 AS builder

WORKDIR /app

# Copy pom.xml (not downloading dependencies)
COPY pom.xml .

# Copy pre-built jar from local target directory
COPY target/format-converter.jar /app/format-converter.jar

# Runtime stage
FROM eclipse-temurin:11-jre-alpine

WORKDIR /app

# Copy the built jar
COPY --from=builder /app/format-converter.jar app.jar

# Environment variables
ENV KAFKA_BOOTSTRAP_SERVERS=kafka:9092
ENV INPUT_TOPIC=sw-traces
ENV OUTPUT_TOPIC=otlp-traces
ENV CONSUMER_GROUP_ID=format-converter

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
