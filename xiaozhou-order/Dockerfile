# Use pre-built JAR from local build
FROM eclipse-temurin:8-jre-alpine

# Install required tools
RUN apk add --no-cache tar
WORKDIR /app

# Copy and extract SkyWalking Agent
COPY skywalking-agent/apache-skywalking-java-agent-9.5.0.tgz /app/
RUN tar -xzf /app/apache-skywalking-java-agent-9.5.0.tgz -C /app/ && rm /app/apache-skywalking-java-agent-9.5.0.tgz

# Kafka Reporter is disabled - use gRPC to send traces to otel-collector

# Create log directory
RUN mkdir -p /var/log/apps/xiaozhou-order

# Copy the pre-built JAR from local target directory
COPY xiaozhou-order/target/xiaozhou-order-0.0.1-SNAPSHOT.jar app.jar

EXPOSE 8089
ENTRYPOINT ["java", "-javaagent:/app/skywalking-agent/skywalking-agent.jar", "-Xmx256m", "-jar", "app.jar"]
