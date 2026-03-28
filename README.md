# OpenTelemetry + Data Prepper + OpenSearch 可观测性平台

## 整体架构流程

```
┌─────────────────┐     ┌─────────────────────┐     ┌─────────────────┐     ┌──────────────┐     ┌─────────────────────┐
│   业务应用       │     │ OpenTelemetry       │     │   Data Prepper  │     │  OpenSearch  │     │ OpenSearch        │
│ (Java/Python)   │────▶│     Collector       │────▶│                 │────▶│              │────▶│ Dashboards        │
│                 │ OTLP│                     │ OTLP│                 │     │              │     │                   │
│ - Traces        │     │ - 接收              │     │ - Trace 拆分    │     │ - 存储       │     │ - 追踪查询        │
│ - Metrics       │     │ - 批处理            │     │ - 服务地图      │     │ - 索引       │     │ - 服务拓扑        │
│ - Logs          │     │ - 过滤              │     │ - Metrics 转换  │     │ - 搜索       │     │ - 日志关联        │
│                 │     │ - 添加资源属性      │     │                 │     │              │     │                   │
└─────────────────┘     └─────────────────────┘     └─────────────────┘     └──────────────┘     └─────────────────────┘
```

## 架构组件说明

### 1. 应用侧 (Application)
业务应用通过 **OpenTelemetry SDK** 或 **Java Agent** 生成可观测性数据：
- **Traces**: 分布式追踪数据
- **Metrics**: 应用指标数据
- **Logs**: 应用日志数据

数据通过 **OTLP (OpenTelemetry Protocol)** 协议发送给 OpenTelemetry Collector。

### 2. OpenTelemetry Collector
作为代理或网关，负责：
- 接收来自应用的 OTLP 数据
- 数据批处理（batch）
- 数据过滤和采样
- 添加资源属性（如 K8s 标签、环境信息）
- 将处理后的数据转发给 Data Prepper

### 3. Data Prepper
核心处理组件，负责：
- **Trace 数据处理**:
  - 原始 Trace 数据流 → 存储到 `otel-v1-apm-span-*` 索引
  - 服务地图数据流 → 生成拓扑图，存储到 `otel-v1-apm-service-map-*` 索引
- **Metrics 数据处理**: 转换为适合 OpenSearch 的格式
- **Logs 数据处理**: 结构化日志存储到 `logs-otel-*` 索引

### 4. OpenSearch
存储处理后的可观测性数据：
- `otel-v1-apm-span-*`: Span 追踪数据
- `otel-v1-apm-service-map-*`: 服务地图数据
- `metrics-otel-*`: 指标数据
- `logs-otel-*`: 日志数据

### 5. OpenSearch Dashboards
使用内置的 **Observability** 插件进行：
- 追踪查询和展示
- 服务拓扑图生成
- 日志搜索和分析
- 指标可视化

---

## 快速开始

### 环境要求
- Docker 20.10+
- Docker Compose 2.0+
- Java 17+ (用于构建应用)
- Maven 3.8+

### 启动服务

```bash
# 构建并启动所有服务
docker-compose up -d --build

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| Nacos | 8848 | 服务注册中心 |
| MySQL | 3306 | 数据库 |
| OpenSearch | 9200 | 搜索引擎 |
| OpenSearch Dashboards | 5601 | 可视化界面 |
| Neo4j | 7474/7687 | 图数据库 |
| OTel Collector | 4317/4318 | OTLP 接收端 |
| Data Prepper | 21890/21891/21892 | 数据处理 |

### 应用接入

#### Java 应用 (使用 Java Agent)

```bash
java -javaagent:/path/to/opentelemetry-javaagent.jar \
     -Dotel.service.name=my-application \
     -Dotel.exporter.otlp.endpoint=http://otel-collector:4317 \
     -jar application.jar
```

#### Spring Boot 应用配置

```yaml
# application.yml
spring:
  application:
    name: my-service

management:
  endpoints:
    web:
      exposure:
        include: health,info,prometheus
  metrics:
    export:
      prometheus:
        enabled: true
```

#### Docker Compose 环境变量

```yaml
services:
  my-app:
    environment:
      - OTEL_SERVICE_NAME=my-app
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
      - OTEL_RESOURCE_ATTRIBUTES=deployment.environment=production
```

---

## 配置说明

### OpenTelemetry Collector 配置

配置文件：`otel-collector-config-running.yaml`

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 10s
    send_batch_size: 1024
  resource:
    attributes:
      - key: deployment.environment
        value: "production"
        action: insert

exporters:
  otlp/dataprepper:
    endpoint: data-prepper:21890
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch, resource]
      exporters: [otlp/dataprepper]
    metrics:
      receivers: [otlp]
      processors: [batch, resource]
      exporters: [otlp/dataprepper]
    logs:
      receivers: [otlp]
      processors: [batch, resource]
      exporters: [otlp/dataprepper]
```

### Data Prepper 配置

配置文件：`data-prepper/pipelines.yaml`

主要管道：
- `otel-trace-pipeline`: 接收 OTLP Trace 数据
- `raw-trace-pipeline`: 处理原始 Span 数据
- `service-map-pipeline`: 生成服务地图
- `otel-metrics-pipeline`: 处理指标数据
- `otel-logs-pipeline`: 处理日志数据

---

## OpenSearch Dashboards 使用

### 访问地址
http://localhost:5601

### 配置索引模式

1. 进入 **Discover** 页面
2. 创建索引模式：
   - `otel-v1-apm-span-*` (追踪数据)
   - `otel-v1-apm-service-map-*` (服务地图)
   - `logs-otel-*` (日志数据)
   - `metrics-otel-*` (指标数据)

### 使用 Observability 插件

1. 进入 **Observability** → **Traces**
2. 选择服务名称和时间范围
3. 查看追踪瀑布图和服务拓扑

---

## 常见问题

### 1. 数据未显示
- 检查应用是否正确配置 OTLP 导出端点
- 确认 OTel Collector 和 Data Prepper 服务正常运行
- 检查 OpenSearch 索引是否正确创建

### 2. 性能优化
- 调整 OTel Collector 的 batch 配置
- 增加 Data Prepper 的 buffer 大小
- 优化 OpenSearch 索引模板和分片设置

### 3. 日志关联
确保 Trace ID 正确传递到日志中：
```java
// 使用 OpenTelemetry 的 MDC 集成
OpenTelemetrySdk.getGlobalLogsSdkProvider()
    .addBatchLogRecordProcessor();
```

---

## 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

---

## 参考资源

- [OpenTelemetry 官方文档](https://opentelemetry.io/docs/)
- [Data Prepper 官方文档](https://opensearch.org/docs/latest/data-prepper/index/)
- [OpenSearch Observability](https://opensearch.org/docs/latest/observability/index/)