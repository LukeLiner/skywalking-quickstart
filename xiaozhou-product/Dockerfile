# Stage 1: Build the application
FROM maven:3.6.3-jdk-8-slim AS build
WORKDIR /app

# Copy the parent pom and the product module
COPY pom.xml .
COPY xiaozhou-product/pom.xml xiaozhou-product/
# Copy other modules if they are dependencies
COPY xiaozhou-order/pom.xml xiaozhou-order/

# Build dependencies
RUN mvn dependency:go-offline -B -f pom.xml

# Copy the source code
COPY xiaozhou-product/src xiaozhou-product/src

# Package the application
RUN mvn clean package -DskipTests -pl xiaozhou-product -am

# Stage 2: Run the application
FROM openjdk:8-jdk-alpine
WORKDIR /app

# Download SkyWalking Agent
ENV SW_AGENT_VERSION=9.5.0
RUN wget https://archive.apache.org/dist/skywalking/java-agent/$SW_AGENT_VERSION/apache-skywalking-java-agent-$SW_AGENT_VERSION.tgz && \
    tar -zxvf apache-skywalking-java-agent-$SW_AGENT_VERSION.tgz && \
    rm apache-skywalking-java-agent-$SW_AGENT_VERSION.tgz

COPY --from=build /app/xiaozhou-product/target/xiaozhou-product-0.0.1-SNAPSHOT.jar app.jar

EXPOSE 8090
ENTRYPOINT ["java", "-javaagent:/app/skywalking-agent/skywalking-agent.jar", "-Xmx256m", "-jar", "app.jar"]
