package com.converter.service;

import com.converter.converter.SkyWalkingToOtlpConverter;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import io.opentelemetry.proto.collector.trace.v1.ExportTraceServiceRequest;
import io.opentelemetry.proto.collector.trace.v1.TraceServiceGrpc;
import org.apache.skywalking.apm.network.language.agent.v3.SegmentObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

import java.util.concurrent.atomic.AtomicLong;

/**
 * Service that consumes SkyWalking trace segments from Kafka,
 * converts them to OTLP format, and produces to another topic or OTLP endpoint
 */
@Service
public class TraceConversionService {

    private static final Logger logger = LoggerFactory.getLogger(TraceConversionService.class);

    private final SkyWalkingToOtlpConverter converter;
    private final KafkaTemplate<String, byte[]> kafkaTemplate;

    @Value("${converter.output.topic:otlp-spans}")
    private String outputTopic;

    @Value("${converter.output.otlp_endpoint:http://otel-collector:4317}")
    private String otlpEndpoint;

    private ManagedChannel otlpChannel;
    private TraceServiceGrpc.TraceServiceBlockingStub otlpStub;

    private final AtomicLong processedCount = new AtomicLong(0);
    private final AtomicLong errorCount = new AtomicLong(0);

    @Autowired
    public TraceConversionService(SkyWalkingToOtlpConverter converter, 
                                   KafkaTemplate<String, byte[]> kafkaTemplate) {
        this.converter = converter;
        this.kafkaTemplate = kafkaTemplate;
    }

    /**
     * Initialize OTLP gRPC channel
     */
    private void initOtlpChannel() {
        if (otlpChannel == null || otlpChannel.isShutdown()) {
            try {
                // Parse endpoint to get host and port
                String host = otlpEndpoint.replace("http://", "").replace("https://", "");
                int port = 4317;
                if (host.contains(":")) {
                    String[] parts = host.split(":");
                    host = parts[0];
                    port = Integer.parseInt(parts[1]);
                }
                
                otlpChannel = ManagedChannelBuilder.forAddress(host, port)
                        .usePlaintext()
                        .build();
                otlpStub = TraceServiceGrpc.newBlockingStub(otlpChannel);
                logger.info("Initialized OTLP channel to {}:{}", host, port);
            } catch (Exception e) {
                logger.error("Failed to initialize OTLP channel: {}", e.getMessage());
            }
        }
    }

    /**
     * Listen for SkyWalking trace segments from Kafka
     */
    @KafkaListener(topics = "${converter.input.topic:sw-traces}", 
                   groupId = "${converter.consumer.group-id:format-converter}")
    public void consumeAndConvert(byte[] message) {
        try {
            // Parse SkyWalking SegmentObject from protobuf bytes
            SegmentObject segment = SegmentObject.parseFrom(message);
            
            logger.debug("Received segment: traceId={}, service={}", 
                        segment.getTraceId(), segment.getService());

            // Convert to OTLP format
            ExportTraceServiceRequest otlpRequest = converter.convert(segment);

            // Send to OTLP endpoint (gRPC)
            try {
                initOtlpChannel();
                if (otlpStub != null) {
                    otlpStub.export(otlpRequest);
                    long count = processedCount.incrementAndGet();
                    if (count % 100 == 0) {
                        logger.info("Processed {} segments (OTLP), errors: {}", 
                                   count, errorCount.get());
                    }
                }
            } catch (Exception e) {
                logger.warn("Failed to send to OTLP endpoint, trying Kafka: {}", e.getMessage());
                // Fallback to Kafka
                byte[] otlpBytes = otlpRequest.toByteArray();
                kafkaTemplate.send(outputTopic, segment.getTraceId(), otlpBytes)
                        .addCallback(
                                result -> {
                                    long count = processedCount.incrementAndGet();
                                    if (count % 100 == 0) {
                                        logger.info("Processed {} segments (Kafka), errors: {}", 
                                                   count, errorCount.get());
                                    }
                                },
                                ex -> {
                                    errorCount.incrementAndGet();
                                    logger.error("Failed to send to Kafka {}: {}", 
                                               outputTopic, ex.getMessage());
                                }
                        );
            }

        } catch (Exception e) {
            errorCount.incrementAndGet();
            logger.error("Failed to process message: {}", e.getMessage(), e);
        }
    }

    public long getProcessedCount() {
        return processedCount.get();
    }

    public long getErrorCount() {
        return errorCount.get();
    }
}
