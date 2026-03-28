# Use pre-built JAR from local build
FROM eclipse-temurin:17-jre-alpine

# Install required tools
RUN apk add --no-cache tar
WORKDIR /app

# Download OpenTelemetry Java Agent
RUN wget -q https://github.com/open-telemetry/opentelemetry-java-instrumentation/releases/download/v1.32.0/opentelemetry-javaagent.jar -O /app/opentelemetry-javaagent.jar

# Create log directory
RUN mkdir -p /var/log/apps/xiaozhou-stock

# Copy the pre-built JAR from local target directory
COPY xiaozhou-stock/target/xiaozhou-stock-0.0.1-SNAPSHOT.jar app.jar

EXPOSE 8091
ENTRYPOINT ["java", "-javaagent:/app/opentelemetry-javaagent.jar", "-Xmx256m", "-jar", "app.jar"]