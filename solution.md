# OpenSearch 日志索引为空问题排查与解决方案

## 问题描述

在 OpenSearch 中新建了日志索引 `logs-otel-2026.03.29`，但索引内容为空。

## 问题排查思路

### 1. 数据流分析

```
Java 应用 (xiaozhou-order/product/stock)
    ↓ OTLP 日志导出
OTel Collector (端口 4318 HTTP)
    ↓ logs pipeline
Data Prepper (端口 21892)
    ↓ opensearch sink
OpenSearch (索引 logs-otel-2026.03.29)
```

### 2. 配置文件检查

#### 2.1 Data Prepper 配置 ✅ 正确

文件：`data-prepper/pipelines.yaml`

```yaml
otel-logs-pipeline:
  source:
    otel_logs_source:
      port: 21892
      ssl: false
  sink:
    - opensearch:
        hosts:
          - "http://opensearch:9200"
        index_type: custom
        index: "logs-otel-%{yyyy.MM.dd}"
```

**结论**：`index_type: custom` 配置是正确的，只要提供了 `index` 参数即可。根据 Data Prepper 官方文档，这是标准的自定义索引配置方式。

#### 2.2 OTel Collector 配置 ✅ 正确

文件：`otel-collector-config.yaml`

```yaml
exporters:
  otlp/dataprepper-logs:
    endpoint: data-prepper:21892
    tls:
      insecure: true

service:
  pipelines:
    logs:
      receivers: [otlp]
      processors: [resource, transform/logs, batch]
      exporters: [otlp/dataprepper-logs]
```

#### 2.3 Java 应用环境变量 ✅ 正确

文件：`docker-compose.yml`

```yaml
xiaozhou-order:
  environment:
    - OTEL_LOGS_EXPORTER=otlp
    - OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=http://otel-collector:4318
    - OTEL_EXPORTER_OTLP_LOGS_PROTOCOL=http/protobuf
```

### 3. 根本原因 ❌

**Java 应用没有配置 OpenTelemetry Logback Appender**

虽然 docker-compose.yml 中设置了 `OTEL_LOGS_EXPORTER=otlp`，但 OpenTelemetry Java Agent 1.32.0 **默认不会自动采集应用日志**。需要额外配置 logback appender 才能将日志发送到 OTLP 端点。

当前 logback 配置（`logback-spring.xml`）只有：
- Console appender - 输出到控制台
- File appender - 输出到文件

**缺少**：OpenTelemetry Logback Appender 配置

---

## 解决方案

### 方案一（推荐）：添加 OpenTelemetry Logback Appender

#### 步骤 1：修改 pom.xml 添加依赖

在 `xiaozhou-order/pom.xml`、`xiaozhou-product/pom.xml`、`xiaozhou-stock/pom.xml` 中添加：

```xml
<dependency>
    <groupId>io.opentelemetry.instrumentation</groupId>
    <artifactId>opentelemetry-logback-appender-1.32.0</artifactId>
    <version>1.32.0-alpha</version>
</dependency>
```

#### 步骤 2：修改 logback-spring.xml 配置 OTel Appender

在 `logback-spring.xml` 中添加：

```xml
<!-- OpenTelemetry Logback Appender -->
<appender name="otel" class="io.opentelemetry.instrumentation.logback.appender.v1_0.OpenTelemetryAppender">
</appender>

<root level="INFO">
    <appender-ref ref="console"/>
    <appender-ref ref="file"/>
    <appender-ref ref="otel"/>  <!-- 添加这一行 -->
</root>
```

#### 步骤 3：重新构建并部署

```bash
docker-compose build xiaozhou-order xiaozhou-product xiaozhou-stock
docker-compose up -d
```

### 方案二：使用文件日志采集（备选）

如果不想修改 Java 应用代码，可以启用 OTel Collector 的 filelog receiver：

1. 取消 `otel-collector-config.yaml` 中 filelog receiver 的注释
2. 确保 Java 应用将日志写入文件（当前已配置）
3. 挂载日志目录到 OTel Collector

---

## 验证步骤

1. 检查 Data Prepper 日志：
   ```bash
   docker logs data-prepper
   ```

2. 检查 OTel Collector 日志：
   ```bash
   docker logs otel-collector
   ```

3. 验证索引是否有数据：
   ```bash
   curl -X GET "http://localhost:9200/logs-otel-2026.03.29/_count"
   ```

---

## 总结

| 组件 | 配置状态 | 说明 |
|------|----------|------|
| Data Prepper | ✅ 正确 | `index_type: custom` 配置正确 |
| OTel Collector | ✅ 正确 | logs pipeline 正确配置 |
| Java 应用 | ❌ 缺少配置 | 缺少 logback-otel-appender |

**问题不在 Data Prepper 的 `index_type` 配置，而是 Java 应用没有配置日志发送组件。**