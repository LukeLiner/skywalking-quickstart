# xiaozhou-order 日志采集失败问题分析与修复

## 问题描述

xiaozhou-order 容器启动后，日志采集失败，错误信息如下：

```
[otel.javaagent 2026-03-29 14:45:25:519 +0000] [OkHttp http://otel-collector:4318/...] 
WARN io.opentelemetry.exporter.internal.http.HttpExporter - 
Failed to export logs. Server responded with HTTP status code 404. 
Error message: Unable to parse response body, HTTP status message: Not Found
```

## 根本原因

**Dockerfile 中的环境变量配置与 docker-compose.yml 冲突**

### 问题配置对比

| 配置文件 | 环境变量 | 值 |
|---------|---------|-----|
| xiaozhou-order/Dockerfile | `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://otel-collector:4317` |
| xiaozhou-order/Dockerfile | `OTEL_SERVICE_NAME` | `xiaozhou-order` |
| docker-compose.yml | `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT` | `http://otel-collector:4318` |
| docker-compose.yml | `OTEL_SERVICE_NAME` | `xiaozhou-order` |

Dockerfile 中的 `OTEL_EXPORTER_OTLP_ENDPOINT` 会覆盖 docker-compose.yml 中的更具体配置 (`OTEL_EXPORTER_OTLP_LOGS_ENDPOINT`)，导致日志被发送到错误的端点（4317 而不是 4318）。

### 其他服务检查结果

| 服务 | Dockerfile 是否有问题 |
|------|----------------------|
| xiaozhou-order | ❌ 有问题 - 设置了 `OTEL_EXPORTER_OTLP_ENDPOINT` 和 `OTEL_SERVICE_NAME` |
| xiaozhou-product | ✅ 正常 - 没有设置 OTEL 环境变量 |
| xiaozhou-stock | ✅ 正常 - 没有设置 OTEL 环境变量 |

## 修复方案

### 修改 xiaozhou-order/Dockerfile

移除以下两行：

```dockerfile
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
ENV OTEL_SERVICE_NAME=xiaozhou-order
```

修改后的 Dockerfile 相关部分应该是：

```dockerfile
# Copy the pre-built JAR from local target directory
COPY xiaozhou-order/target/xiaozhou-order-0.0.1-SNAPSHOT.jar app.jar

# Set OpenTelemetry environment variables - 移除这些行
# ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
# ENV OTEL_SERVICE_NAME=xiaozhou-order

EXPOSE 8089
ENTRYPOINT ["java", "-javaagent:/app/opentelemetry-javaagent.jar", "-Xmx256m", "-jar", "app.jar"]
```

### 修复后效果

- docker-compose.yml 中的环境变量配置将生效
- 日志将正确发送到 `http://otel-collector:4318`
- OTLP 协议使用 `http/protobuf`

## 附加问题

应用还因 Nacos 未启动而无法注册服务：

```
com.alibaba.nacos.api.exception.NacosException: 
failed to req API:/nacos/v1/ns/instance after all servers([nacos:8848]) tried: 
java.net.ConnectException: Connection refused
```

**解决方案**：确保启动顺序正确，先启动 Nacos 等依赖服务。

## 验证步骤

1. 修复 Dockerfile 后重新构建镜像
2. 确保 Nacos 服务先于 xiaozhou-order 启动
3. 启动 xiaozhou-order 容器
4. 检查日志中是否还有 404 错误
5. 确认日志成功发送到 otel-collector

---

*文档生成时间：2026-03-29*