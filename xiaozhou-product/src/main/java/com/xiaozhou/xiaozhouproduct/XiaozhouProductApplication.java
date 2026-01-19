package com.xiaozhou.xiaozhouproduct;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.openfeign.EnableFeignClients;

@EnableDiscoveryClient
@SpringBootApplication
@EnableFeignClients(basePackages = "com.xiaozhou.xiaozhouproduct.feign")
public class XiaozhouProductApplication {

	public static void main(String[] args) {
		SpringApplication.run(XiaozhouProductApplication.class, args);
	}

}
