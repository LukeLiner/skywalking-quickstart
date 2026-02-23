package com.xiaozhou.xiaozhoustock.consumer;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.xiaozhou.xiaozhoustock.entity.Stock;
import com.xiaozhou.xiaozhoustock.mapper.StockMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.messaging.handler.annotation.Header;
import org.springframework.stereotype.Component;

import javax.annotation.Resource;
import java.util.Map;

@Component
public class OrderConsumer {

    private static final Logger logger = LoggerFactory.getLogger(OrderConsumer.class);

    @Resource
    private StockMapper stockMapper;

    private final ObjectMapper objectMapper = new ObjectMapper();

    @KafkaListener(topics = "order-stock-topic", groupId = "stock-group")
    public void consumeOrderMessage(String message, 
            @Header(name = "x-trace-id", required = false) String traceIdFromHeader) {
        try {
            logger.info("Received order message from Kafka: {}", message);

            // Parse the JSON message
            Map<String, Object> orderData = objectMapper.readValue(message, Map.class);

            // Extract traceId from message body
            String traceId = (String) orderData.get("traceId");
            
            // Also check header if not in body
            if (traceId == null && traceIdFromHeader != null) {
                traceId = traceIdFromHeader;
            }
            
            if (traceId != null) {
                logger.info("Received message with traceId: {}", traceId);
            }

            Long productId = Long.valueOf(orderData.get("productId").toString());
            Integer quantity = Integer.valueOf(orderData.get("quantity").toString());
            String orderId = orderData.get("orderId").toString();

            logger.info("Processing order: orderId={}, productId={}, quantity={}, traceId={}", 
                    orderId, productId, quantity, traceId);

            // Mock stock decrease logic
            decreaseStock(productId, quantity, orderId);

        } catch (Exception e) {
            logger.error("Error processing order message: {}", e.getMessage(), e);
        }
    }

    /**
     * Mock stock decrease logic
     * In a real scenario, this would update the database
     */
    private void decreaseStock(Long productId, Integer quantity, String orderId) {
        // Mock: decrease stock by quantity
        // In real implementation, you would use stockMapper to update the database
        
        logger.info("Mock: Decreasing stock for productId={}, quantity={}, orderId={}", 
                    productId, quantity, orderId);

        // Simulate database update
        Stock stock = stockMapper.selectById(productId);
        if (stock != null) {
            Integer newStock = stock.getStockQuantity() - quantity;
            stock.setStockQuantity(newStock);
            stockMapper.updateById(stock);
            logger.info("Stock updated: productId={}, newStockQuantity={}", productId, newStock);
        } else {
            // For mock - create a mock stock record if not exists
            logger.warn("Stock record not found for productId={}, creating mock record", productId);
            Stock mockStock = new Stock();
            mockStock.setProductId(productId);
            mockStock.setProductName("Mock Product " + productId);
            mockStock.setStockQuantity(1000 - quantity); // Start with 1000, decrease by quantity
            mockStock.setReservedStock(0);
            stockMapper.insert(mockStock);
            logger.info("Created mock stock: productId={}, stockQuantity={}", productId, mockStock.getStockQuantity());
        }
    }
}
