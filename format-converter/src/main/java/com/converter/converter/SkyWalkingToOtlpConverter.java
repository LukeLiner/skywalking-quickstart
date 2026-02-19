package com.converter.converter;

import io.opentelemetry.proto.collector.trace.v1.ExportTraceServiceRequest;
import io.opentelemetry.proto.common.v1.AnyValue;
import io.opentelemetry.proto.common.v1.InstrumentationScope;
import io.opentelemetry.proto.common.v1.KeyValue;
import io.opentelemetry.proto.resource.v1.Resource;
import io.opentelemetry.proto.trace.v1.*;
import org.apache.skywalking.apm.network.common.v3.KeyStringValuePair;
import org.apache.skywalking.apm.network.language.agent.v3.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;

/**
 * Converts SkyWalking trace segment format to OpenTelemetry OTLP format
 */
@Component
public class SkyWalkingToOtlpConverter {

    private static final Logger logger = LoggerFactory.getLogger(SkyWalkingToOtlpConverter.class);

    /**
     * Convert SkyWalking SegmentObject to OTLP ExportTraceServiceRequest
     */
    public ExportTraceServiceRequest convert(SegmentObject segment) {
        try {
            // Build Resource with service info
            Resource resource = Resource.newBuilder()
                    .addAttributes(KeyValue.newBuilder()
                            .setKey("service.name")
                            .setValue(AnyValue.newBuilder().setStringValue(segment.getService()).build())
                            .build())
                    .addAttributes(KeyValue.newBuilder()
                            .setKey("service.instance.id")
                            .setValue(AnyValue.newBuilder().setStringValue(segment.getServiceInstance()).build())
                            .build())
                    .build();

            // Convert spans
            List<Span> otlpSpans = new ArrayList<>();
            for (SpanObject swSpan : segment.getSpansList()) {
                otlpSpans.add(convertSpan(swSpan, segment.getTraceId(), segment.getTraceSegmentId()));
            }

            // Build ScopeSpans
            ScopeSpans scopeSpans = ScopeSpans.newBuilder()
                    .setScope(InstrumentationScope.newBuilder()
                            .setName("skywalking-converter")
                            .setVersion("1.0.0")
                            .build())
                    .addAllSpans(otlpSpans)
                    .build();

            // Build ResourceSpans
            ResourceSpans resourceSpans = ResourceSpans.newBuilder()
                    .setResource(resource)
                    .addScopeSpans(scopeSpans)
                    .build();

            return ExportTraceServiceRequest.newBuilder()
                    .addResourceSpans(resourceSpans)
                    .build();

        } catch (Exception e) {
            logger.error("Failed to convert SkyWalking segment to OTLP", e);
            throw new RuntimeException("Conversion failed", e);
        }
    }

    /**
     * Convert SkyWalking SpanObject to OTLP Span
     */
    private Span convertSpan(SpanObject swSpan, String traceId, String segmentId) {
        Span.Builder spanBuilder = Span.newBuilder()
                .setTraceId(hexStringToByteString(traceId))
                .setSpanId(generateSpanId(segmentId, swSpan.getSpanId()))
                .setName(swSpan.getOperationName())
                .setKind(convertSpanKind(swSpan.getSpanType()))
                .setStartTimeUnixNano(swSpan.getStartTime() * 1_000_000L)
                .setEndTimeUnixNano(swSpan.getEndTime() * 1_000_000L);

        // Set parent span ID if exists
        if (swSpan.getParentSpanId() >= 0) {
            spanBuilder.setParentSpanId(generateSpanId(segmentId, swSpan.getParentSpanId()));
        }

        // Set status based on isError
        if (swSpan.getIsError()) {
            spanBuilder.setStatus(Status.newBuilder()
                    .setCode(Status.StatusCode.STATUS_CODE_ERROR)
                    .build());
        } else {
            spanBuilder.setStatus(Status.newBuilder()
                    .setCode(Status.StatusCode.STATUS_CODE_OK)
                    .build());
        }

        // Convert tags to attributes
        for (KeyStringValuePair tag : swSpan.getTagsList()) {
            spanBuilder.addAttributes(KeyValue.newBuilder()
                    .setKey(tag.getKey())
                    .setValue(AnyValue.newBuilder().setStringValue(tag.getValue()).build())
                    .build());
        }

        // Add SkyWalking specific attributes
        spanBuilder.addAttributes(KeyValue.newBuilder()
                .setKey("sw.component")
                .setValue(AnyValue.newBuilder().setStringValue(swSpan.getComponentId() + "").build())
                .build());

        spanBuilder.addAttributes(KeyValue.newBuilder()
                .setKey("sw.peer")
                .setValue(AnyValue.newBuilder().setStringValue(swSpan.getPeer()).build())
                .build());

        // Convert logs to events
        for (Log log : swSpan.getLogsList()) {
            Span.Event.Builder eventBuilder = Span.Event.newBuilder()
                    .setTimeUnixNano(log.getTime() * 1_000_000L);
            
            for (KeyStringValuePair data : log.getDataList()) {
                eventBuilder.addAttributes(KeyValue.newBuilder()
                        .setKey(data.getKey())
                        .setValue(AnyValue.newBuilder().setStringValue(data.getValue()).build())
                        .build());
            }
            spanBuilder.addEvents(eventBuilder.build());
        }

        return spanBuilder.build();
    }

    /**
     * Convert SkyWalking SpanType to OTLP SpanKind
     */
    private Span.SpanKind convertSpanKind(SpanType swType) {
        switch (swType) {
            case Entry:
                return Span.SpanKind.SPAN_KIND_SERVER;
            case Exit:
                return Span.SpanKind.SPAN_KIND_CLIENT;
            case Local:
            default:
                return Span.SpanKind.SPAN_KIND_INTERNAL;
        }
    }

    /**
     * Convert hex string trace ID to ByteString (padded to 16 bytes)
     */
    private com.google.protobuf.ByteString hexStringToByteString(String hex) {
        // Remove dots and special chars from SkyWalking trace ID
        String cleanHex = hex.replaceAll("[^a-fA-F0-9]", "");
        
        // Ensure 32 hex chars (16 bytes) for trace ID
        while (cleanHex.length() < 32) {
            cleanHex = "0" + cleanHex;
        }
        if (cleanHex.length() > 32) {
            cleanHex = cleanHex.substring(cleanHex.length() - 32);
        }
        
        byte[] bytes = new byte[16];
        for (int i = 0; i < 16; i++) {
            bytes[i] = (byte) Integer.parseInt(cleanHex.substring(i * 2, i * 2 + 2), 16);
        }
        return com.google.protobuf.ByteString.copyFrom(bytes);
    }

    /**
     * Generate 8-byte span ID from segment ID and span index
     */
    private com.google.protobuf.ByteString generateSpanId(String segmentId, int spanIndex) {
        String combined = segmentId + "-" + spanIndex;
        int hash = combined.hashCode();
        byte[] bytes = new byte[8];
        for (int i = 0; i < 4; i++) {
            bytes[i] = (byte) (hash >> (i * 8));
            bytes[i + 4] = (byte) (spanIndex >> (i * 8));
        }
        return com.google.protobuf.ByteString.copyFrom(bytes);
    }
}
