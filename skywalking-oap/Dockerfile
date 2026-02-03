# SkyWalking OAP with MySQL driver and Exporter configuration
FROM apache/skywalking-oap-server:9.3.0

# Download MySQL Connector/J using curl
ENV MYSQL_CONNECTOR_VERSION=8.0.28
RUN curl -L https://repo1.maven.org/maven2/mysql/mysql-connector-java/${MYSQL_CONNECTOR_VERSION}/mysql-connector-java-${MYSQL_CONNECTOR_VERSION}.jar \
    -o /skywalking/oap-libs/mysql-connector-java-${MYSQL_CONNECTOR_VERSION}.jar

# Copy custom exporter configuration
COPY skywalking-oap/exporter.yaml /skywalking/config/exporter.yaml
