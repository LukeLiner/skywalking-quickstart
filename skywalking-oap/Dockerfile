# SkyWalking OAP with OpenSearch storage
FROM apache/skywalking-oap-server:9.3.0

# Copy custom application.yml with OpenSearch storage and Kafka configuration
COPY skywalking-oap/application.yml /skywalking/config/application.yml
# Copy MySQL connector (though we use OpenSearch storage, some components may still reference MySQL)
COPY skywalking-oap/mysql-connector-java-8.0.28.jar /skywalking/oap-libs/mysql-connector-java-8.0.28.jar
