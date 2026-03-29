# xiaozhou-product / xiaozhou-stock Logback 配置错误排查

## 问题描述

xiaozhou-product 容器启动失败，日志报错：

```
java.lang.ClassNotFoundException: org.apache.skywalking.apm.toolkit.log.logback.v1.x.TraceIdPatternLogbackLayout
java.lang.ClassNotFoundException: org.apache.skywalking.apm.toolkit.log.logback.v1.x.mdc.TraceIdMDCPatternLogbackLayout
```

## 错误日志完整信息

```
Exception in thread "main" java.lang.reflect.InvocationTargetException
    at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
    ...
Caused by: java.lang.IllegalStateException: Logback configuration error detected:
ERROR in ch.qos.logback.core.joran.action.NestedComplexPropertyIA - 
Could not create component [layout] of type 
[org.apache.skywalking.apm.toolkit.log.logback.v1.x.TraceIdPatternLogbackLayout] 
java.lang.ClassNotFoundException: org.apache.skywalking.apm.toolkit.log.logback.v1.x.TraceIdPatternLogbackLayout

ERROR in ch.qos.logback.core.joran.action.NestedComplexPropertyIA - 
Could not create component [layout] of type 
[org.apache.skywalking.apm.toolkit.log.logback.v1.x.mdc.TraceIdMDCPatternLogbackLayout] 
java.lang.ClassNotFoundException: org.apache.skywalking.apm.toolkit.log.logback.v1.x.mdc.TraceIdMDCPatternLogbackLayout
```

## 根本原因

**logback-spring.xml 配置使用了不存在的 SkyWalking 类**

- `xiaozhou-product` 和 `xiaozhou-stock` 的 `logback-spring.xml` 使用了 SkyWalking 的日志布局类
- 但项目的 `pom.xml` 中**没有添加 SkyWalking 依赖**（只有 OpenTelemetry 依赖）
- 这导致 `ClassNotFoundException`，应用无法启动

## 三个服务配置对比

| 服务 | logback-spring.xml 使用 SkyWalking 类 | pom.xml 有 SkyWalking 依赖 | 状态 |
|------|---------------------------------------|---------------------------|------|
| xiaozhou-order | ❌ 否 | ❌ 无 | ✅ 正常 |
| xiaozhou-product | ✅ 是 | ❌ 无 | ❌ 启动失败 |
| xiaozhou-stock | ✅ 是 | ❌ 无 | ❌ 将会失败 |

## 修复方案

### 1. 修复 xiaozhou-product/src/main/resources/logback-spring.xml

将：

```xml
<appender name="console" class="ch.qos.logback.core.ConsoleAppender">
    <encoder class="ch.qos.logback.core.encoder.LayoutWrappingEncoder">
        <layout class="org.apache.skywalking.apm.toolkit.log.logback.v1.x.TraceIdPatternLogbackLayout">
            <Pattern>${CONSOLE_LOG_PATTERN}</Pattern>
        </layout>
    </encoder>
</appender>
```

改为：

```xml
<appender name="console" class="ch.qos.logback.core.ConsoleAppender">
    <encoder>
        <pattern>${CONSOLE_LOG_PATTERN}</pattern>
    </encoder>
</appender>
```

将文件 appender 中的：

```xml
<encoder class="ch.qos.logback.core.encoder.LayoutWrappingEncoder">
    <layout class="org.apache.skywalking.apm.toolkit.log.logback.v1.x.mdc.TraceIdMDCPatternLogbackLayout">
        <Pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%X{tid}] [%thread] %-5level %logger{36} -%msg%n</Pattern>
    </layout>
</encoder>
```

改为：

```xml
<encoder>
    <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %-5level %logger{36} -%msg%n</pattern>
</encoder>
```

### 2. 修复 xiaozhou-stock/src/main/resources/logback-spring.xml

同上，修改内容相同。

### 3. 移除 CONSOLE_LOG_PATTERN 中的 %tid

原配置：
```xml
<property name="CONSOLE_LOG_PATTERN" value="... %tid ..."/>
```

改为：
```xml
<property name="CONSOLE_LOG_PATTERN" value="%clr(%d{${LOG_DATEFORMAT_PATTERN:-yyyy-MM-dd HH:mm:ss.SSS}}){faint} %clr(${LOG_LEVEL_PATTERN:-%5p}) %clr(${PID:- }){magenta} %clr(---){faint} %clr([%15.15t]){faint} %clr(%-40.40logger{39}){cyan} %clr(:){faint} %m%n${LOG_EXCEPTION_CONVERSION_WORD:-%wEx}"/>
```

## 修复后的正确配置

参考 `xiaozhou-order/src/main/resources/logback-spring.xml`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <include resource="org/springframework/boot/logging/logback/defaults.xml"/>

    <!-- Console Appender with OpenTelemetry TraceId -->
    <property name="CONSOLE_LOG_PATTERN" value="%clr(%d{${LOG_DATEFORMAT_PATTERN:-yyyy-MM-dd HH:mm:ss.SSS}}){faint} %clr(${LOG_LEVEL_PATTERN:-%5p}) %clr(${PID:- }){magenta} %clr(---){faint} %clr([%15.15t]){faint} %clr(%-40.40logger{39}){cyan} %clr(:){faint} %m%n${LOG_EXCEPTION_CONVERSION_WORD:-%wEx}"/>
    <appender name="console" class="ch.qos.logback.core.ConsoleAppender">
        <encoder>
            <pattern>${CONSOLE_LOG_PATTERN}</pattern>
        </encoder>
    </appender>

    <!-- File Appender - 输出日志到文件供 OTel Collector 采集 -->
    <appender name="file" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>/var/log/apps/xiaozhou-product.log</file>
        <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
            <fileNamePattern>/var/log/apps/xiaozhou-product.%d{yyyy-MM-dd}.log</fileNamePattern>
            <maxHistory>7</maxHistory>
        </rollingPolicy>
        <encoder>
            <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %-5level %logger{36} -%msg%n</pattern>
        </encoder>
    </appender>

    <root level="INFO">
        <appender-ref ref="console"/>
        <appender-ref ref="file"/>
    </root>
</configuration>
```

> **注意**：xiaozhou-stock 需要将文件名改为 `xiaozhou-stock.log`

## 验证步骤

1. 修复两个 logback-spring.xml 文件
2. 重新构建 xiaozhou-product 和 xiaozhou-stock 镜像
3. 启动容器
4. 检查日志中是否还有 ClassNotFoundException 错误
5. 确认应用正常启动

---

*文档生成时间：2026-03-29*