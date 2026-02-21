package com.xiaozhou.xiaozhouproduct.feign;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;

@FeignClient(name = "xiaozhou-order", url = "http://xiaozhou-order:8089")
public interface OrderFeign {
    @RequestMapping("/order/getOrder")
    public String getOrderById(@RequestParam("id") String id);
}
