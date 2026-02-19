# Build stage
FROM maven:3.8-openjdk-11 AS builder

WORKDIR /app

# Copy pom.xml and download dependencies
COPY pom.xml .
RUN mvn dependency:go-offline -B

# Copy source and build
COPY src ./src
RUN mvn package -DskipTests -B

# Runtime stage
FROM eclipse-temurin:11-jre-alpine

WORKDIR /app

# Copy the built jar
COPY --from=builder /app/target/format-converter.jar app.jar

# Environment variables
ENV KAFKA_BOOTSTRAP_SERVERS=kafka:9092
ENV INPUT_TOPIC=sw-traces
ENV OUTPUT_TOPIC=otlp-traces
ENV CONSUMER_GROUP_ID=format-converter

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
