package com.converter;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * SkyWalking to OTLP Format Converter Application
 * 
 * This application consumes SkyWalking protobuf messages from Kafka,
 * converts them to OTLP format, and produces to another Kafka topic
 * for OpenTelemetry Collector consumption.
 */
@SpringBootApplication
public class FormatConverterApplication {

    public static void main(String[] args) {
        SpringApplication.run(FormatConverterApplication.class, args);
    }
}
