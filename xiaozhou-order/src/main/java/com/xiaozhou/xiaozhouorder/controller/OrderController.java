package com.xiaozhou.xiaozhouorder.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/order")
public class OrderController {

    private static final Logger logger = LoggerFactory.getLogger(OrderController.class);

    @RequestMapping("/getOrder")
    public String getOrderById(@RequestParam(required = false) String id) throws InterruptedException {
        logger.info("Received getOrder request, orderId={}", id);
        
        long startTime = System.currentTimeMillis();
        Thread.sleep(1000);
        long duration = System.currentTimeMillis() - startTime;
        
        logger.info("Order query completed, orderId={}, duration={}ms", id, duration);
        
        return "orderId:" + id;
    }
}
