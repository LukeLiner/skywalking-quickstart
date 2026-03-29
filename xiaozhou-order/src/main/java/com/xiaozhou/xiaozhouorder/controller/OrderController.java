package com.xiaozhou.xiaozhouorder.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicInteger;

@RestController
@RequestMapping("/order")
public class OrderController {

    private static final Logger logger = LoggerFactory.getLogger(OrderController.class);

    private static final String ORDER_STOCK_TOPIC = "order-stock-topic";

    @Resource
    private KafkaTemplate<String, String> kafkaTemplate;

    private final ObjectMapper objectMapper = new ObjectMapper();
    
    private final AtomicInteger orderCounter = new AtomicInteger(0);

    /**
     * Scheduled task to generate trace data every 3 seconds
     * Simulates getOrder API call for testing trace analytics
     */
    @Scheduled(fixedRate = 3000)
    public void generateTraceData() {
        int orderId = orderCounter.incrementAndGet();
        try {
            getOrderById(String.valueOf(orderId));
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            logger.error("Error generating trace data: {}", e.getMessage());
        }
    }

    @RequestMapping("/getOrder")
    public String getOrderById(@RequestParam(required = false) String id) throws InterruptedException {
        logger.info("Received getOrder request, orderId={}", id);
        
        // Get SkyWalking trace ID for logging
        long startTime = System.currentTimeMillis();
        Thread.sleep(1000);
        long duration = System.currentTimeMillis() - startTime;
        
        logger.info("Order query completed, orderId={}, duration={}ms, traceId={}", id, duration, "");
        
        return "orderId:" + id;
    }

    /**
     * Create a new order - MOCK DATA RETURN
     * 
     * @param productId Product ID
     * @param quantity Quantity to order
     * @return Mock order result
     */
    @RequestMapping("/createOrder")
    public Map<String, Object> createOrder(
            @RequestParam(required = false, defaultValue = "1") Long productId,
            @RequestParam(required = false, defaultValue = "1") Integer quantity) {
        
        Map<String, Object> result = new HashMap<>();
        
        // Mock data return - no actual Kafka processing
        logger.info("Mock createOrder: productId={}, quantity={}", productId, quantity);

        result.put("success", true);
        result.put("orderId", "MOCK-" + UUID.randomUUID().toString().substring(0, 8));
        result.put("productId", productId);
        result.put("quantity", quantity);
        result.put("status", "CREATED");
        result.put("message", "Mock order created successfully");
        result.put("timestamp", System.currentTimeMillis());
        
        return result;
        // try {
        //     // Generate order ID
        //     String orderId = UUID.randomUUID().toString();
        //     logger.info("Creating order: orderId={}, productId={}, quantity={}", orderId, productId, quantity);

        //     // Get current SkyWalking trace ID for logging
        //     String traceId = TraceContext.traceId();
        //     logger.info("Current Trace ID: {}", traceId);

        //     // Create order message
        //     Map<String, Object> orderMessage = new HashMap<>();
        //     orderMessage.put("orderId", orderId);
        //     orderMessage.put("productId", productId);
        //     orderMessage.put("quantity", quantity);
        //     orderMessage.put("timestamp", System.currentTimeMillis());
        //     orderMessage.put("traceId", traceId);

        //     String messageJson = objectMapper.writeValueAsString(orderMessage);

        //     // Send to Kafka with topic and key
        //     kafkaTemplate.send(ORDER_STOCK_TOPIC, orderId, messageJson);
            
        //     logger.info("Order message sent to Kafka: topic={}, orderId={}, traceId={}", 
        //             ORDER_STOCK_TOPIC, orderId, traceId);

        //     // Mark the exit span with the Kafka topic
        //     ActiveSpan.tag("kafka.topic", ORDER_STOCK_TOPIC);
        //     ActiveSpan.tag("kafka.key", orderId);

        //     result.put("success", true);
        //     result.put("orderId", orderId);
        //     result.put("message", "Order created successfully, stock processing async");

        // } catch (Exception e) {
        //     logger.error("Error creating order: {}", e.getMessage(), e);
        //     result.put("success", false);
        //     result.put("message", "Error creating order: " + e.getMessage());
        // }
    }
}
