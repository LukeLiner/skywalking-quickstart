# SkyWalking OAP with MySQL driver and Kafka fetcher configuration
FROM apache/skywalking-oap-server:9.3.0

# Copy pre-downloaded MySQL Connector/J (avoid network issues during build)
COPY skywalking-oap/mysql-connector-java-8.0.28.jar /skywalking/oap-libs/mysql-connector-java-8.0.28.jar

# Use default application.yml - configure via environment variables instead
