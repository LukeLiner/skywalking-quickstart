# Use pre-built JAR from local build
FROM eclipse-temurin:8-jre-alpine

# Install required tools
RUN apk add --no-cache wget tar
WORKDIR /app

# Download SkyWalking Agent
ENV SW_AGENT_VERSION=9.5.0
RUN wget https://archive.apache.org/dist/skywalking/java-agent/$SW_AGENT_VERSION/apache-skywalking-java-agent-$SW_AGENT_VERSION.tgz && \
    tar -zxvf apache-skywalking-java-agent-$SW_AGENT_VERSION.tgz && \
    rm apache-skywalking-java-agent-$SW_AGENT_VERSION.tgz

# Enable Kafka Reporter Plugin
RUN cp /app/skywalking-agent/optional-reporter-plugins/kafka-reporter-plugin-*.jar /app/skywalking-agent/plugins/

# Create log directory
RUN mkdir -p /var/log/apps/xiaozhou-order

# Copy the pre-built JAR from local target directory
COPY xiaozhou-order/target/xiaozhou-order-0.0.1-SNAPSHOT.jar app.jar

EXPOSE 8089
ENTRYPOINT ["java", "-javaagent:/app/skywalking-agent/skywalking-agent.jar", "-Xmx256m", "-jar", "app.jar"]
