package com.xiaozhou.xiaozhouproduct.controller;

import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/sw/alarm")
public class SkywalkingAlarmController {

    /**
     * Skywalking告警通知回调接口：http://127.0.0.1:18081/sw/alarm/notify/
     *
     * @param obj
     * @return
     */
    @RequestMapping("/notify")
    public String notify(@RequestBody Object obj) {
        // TODO 将告警信息通知给负责人。比如：通过发短信，钉钉消息，邮件，微信通知等方式发送给技术负责人
        System.err.println("收到Skywalking告警信息：" + obj.toString());
        return "notify successfully";
    }

}
