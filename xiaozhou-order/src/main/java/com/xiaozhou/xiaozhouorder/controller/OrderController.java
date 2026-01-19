package com.xiaozhou.xiaozhouorder.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/order")
public class OrderController {

    @RequestMapping("/getOrder")
    private String getOrderById(String id) throws InterruptedException {
        Thread.sleep(1000);
        return "orderId:"+id;
    }
}
