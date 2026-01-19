package com.xiaozhou.xiaozhouorder;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;

@SpringBootApplication
@EnableDiscoveryClient
public class XiaozhouOrderApplication {

    public static void main(String[] args) {
        SpringApplication.run(XiaozhouOrderApplication.class, args);
    }

}
