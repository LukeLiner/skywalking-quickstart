# SkyWalking OAP with MySQL storage
FROM apache/skywalking-oap-server:9.3.0

# Add MySQL JDBC driver for MySQL storage
COPY skywalking-oap/mysql-connector-java-8.0.28.jar /skywalking/oap-libs/

# Copy custom application.yml with Kafka configuration
COPY skywalking-oap/application.yml /skywalking/config/application.yml
