# Stage 1: Build the application
FROM maven:3.6.3-jdk-8-slim AS build
WORKDIR /app

# Copy the parent pom and the order module
COPY pom.xml .
COPY xiaozhou-order/pom.xml xiaozhou-order/
# Copy other modules if they are dependencies (they seem to be siblings)
COPY xiaozhou-product/pom.xml xiaozhou-product/

# Build dependencies (this speeds up subsequent builds)
RUN mvn dependency:go-offline -B -f pom.xml

# Copy the source code
COPY xiaozhou-order/src xiaozhou-order/src

# Package the application
RUN mvn clean package -DskipTests -pl xiaozhou-order -am

# Stage 2: Run the application
FROM openjdk:8-jdk-alpine
WORKDIR /app

# Download SkyWalking Agent
ENV SW_AGENT_VERSION=9.5.0
RUN wget https://archive.apache.org/dist/skywalking/java-agent/$SW_AGENT_VERSION/apache-skywalking-java-agent-$SW_AGENT_VERSION.tgz && \
    tar -zxvf apache-skywalking-java-agent-$SW_AGENT_VERSION.tgz && \
    rm apache-skywalking-java-agent-$SW_AGENT_VERSION.tgz

COPY --from=build /app/xiaozhou-order/target/xiaozhou-order-0.0.1-SNAPSHOT.jar app.jar

EXPOSE 8089
ENTRYPOINT ["java", "-javaagent:/app/skywalking-agent/skywalking-agent.jar", "-Xmx256m", "-jar", "app.jar"]
