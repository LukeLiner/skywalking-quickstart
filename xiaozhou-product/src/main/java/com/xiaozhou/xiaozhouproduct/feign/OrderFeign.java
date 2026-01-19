package com.xiaozhou.xiaozhouproduct.feign;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.annotation.RequestMapping;

@FeignClient("xiaozhou-order")            //注册中心上的服务名
public interface OrderFeign {
    @RequestMapping("/order/getOrder")
    public String getOrderById(String id);
}