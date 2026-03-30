# Prometheus Receiver 指标采集配置指南

## 概述

本文档描述了如何使用 OpenTelemetry Collector 的 Prometheus receiver 采集指标数据，并通过 Data Prepper 存储到 OpenSearch。

## 架构流程

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐     ┌─────────────┐
│  Spring Boot    │     │  OTel Collector  │     │   Data      │     │ OpenSearch  │
│  Apps (Microm.  │────▶│  (Prometheus     │────▶│  Prepper    │────▶│  (metrics-  │
│  /actuator/prom │     │   Receiver)      │     │             │     │  otel-*)    │
└─────────────────┘     └──────────────────┘     └─────────────┘     └─────────────┘
        │                        │
        │                        │
   ┌────▼────┐              ┌────▼────┐
   │cAdvisor │              │OTel自采集│
   └─────────┘              └─────────┘
```

## 配置文件说明

### 1. OTel Collector 配置 (`otel-collector-config.yaml`)

#### Receivers

**Prometheus Receiver** - 核心指标采集组件

```yaml
prometheus:
  trim_metric_suffixes: false  # 实验性功能：修剪指标后缀
  config:
    global:
      scrape_interval: 30s     # 全局抓取间隔
      scrape_timeout: 10s      # 全局超时时间
      scrape_native_histograms: false  # 原生直方图支持
      scrape_protocols:        # 支持的协议（按优先级）
        - PrometheusProto
        - OpenMetricsText1.0.0
        - OpenMetricsText0.0.1
        - PrometheusText0.0.4
    
    scrape_configs:
      # 配置多个抓取任务...
```

**配置的抓取目标：**

| Job Name | Target | 路径 | 说明 |
|----------|--------|------|------|
| otel-collector | localhost:8888 | /metrics | OTel Collector 自身指标 |
| xiaozhou-order | xiaozhou-order:8089 | /actuator/prometheus | 订单服务指标 |
| xiaozhou-product | xiaozhou-product:8090 | /actuator/prometheus | 产品服务指标 |
| xiaozhou-stock | xiaozhou-stock:8091 | /actuator/prometheus | 库存服务指标 |
| cadvisor | cadvisor:8080 | /metrics | 容器指标 |

#### Processors

- **resourcedetection**: 自动检测环境信息（env, system）
- **resource**: 添加自定义资源属性（如 deployment.environment）
- **transform/metrics**: 指标转换处理
- **batch**: 批量处理，提高传输效率

#### Exporters

```yaml
otlp/dataprepper-metrics:
  endpoint: data-prepper:21891
  tls:
    insecure: true
  retry_on_failure:
    enabled: true
    initial_interval: 5s
    max_interval: 30s
    max_elapsed_time: 300s
  timeout: 30s
```

#### Service Pipeline

```yaml
metrics:
  receivers: [prometheus]
  processors: [resourcedetection, resource, transform/metrics, batch]
  exporters: [otlp/dataprepper-metrics]
```

### 2. Data Prepper 配置 (`data-prepper/pipelines.yaml`)

```yaml
otel-metrics-pipeline:
  source:
    otel_metrics_source:
      port: 21891
      ssl: false
  buffer:
    bounded_blocking:
      buffer_size: 5120
      batch_size: 512
  processor:
    - otel_metrics_raw_processor:
  sink:
    - opensearch:
        hosts: ["http://opensearch:9200"]
        index_type: custom
        index: "metrics-otel-%{yyyy.MM.dd}"
        bulk_size: 20
        flush_timeout: 30
```

## 快速启动

### 1. 启动服务

```bash
docker-compose up -d
```

### 2. 验证指标采集

检查 OTel Collector 日志：
```bash
docker logs otel-collector | grep prometheus
```

### 3. 验证数据写入

查询 OpenSearch 中的指标索引：
```bash
curl http://localhost:9200/_cat/indices/metrics-otel-*
```

查看指标数据：
```bash
curl http://localhost:9200/metrics-otel-$(date +%Y.%m.%d)/_search?pretty
```

## 配置调优

### 抓取间隔调整

根据指标重要性和系统负载调整 `scrape_interval`：

```yaml
scrape_configs:
  - job_name: 'critical-service'
    scrape_interval: 10s  # 关键服务高频采集
  
  - job_name: 'normal-service'
    scrape_interval: 60s  # 普通服务低频采集
```

### 指标过滤

使用 `metric_relabel_configs` 过滤不需要的指标：

```yaml
metric_relabel_configs:
  # 只保留 JVM 指标
  - source_labels: [__name__]
    regex: "jvm_.*"
    action: keep
  
  # 丢弃某些高基数指标
  - source_labels: [__name__]
    regex: "http_request_duration_seconds_bucket"
    action: drop
```

### 批量处理优化

调整 batch processor 参数：

```yaml
batch:
  timeout: 5s           # 减少延迟
  send_batch_size: 2048 # 增大批次大小
```

## 监控与故障排查

### 1. 查看 Prometheus Receiver 指标

OTel Collector 暴露的自身指标：
```bash
curl http://localhost:8888/metrics | grep prometheus_receiver
```

关键指标：
- `prometheus_receiver_scrapes_total` - 总抓取次数
- `prometheus_receiver_scrape_errors_total` - 抓取错误数
- `prometheus_receiver_scrape_duration_seconds` - 抓取耗时

### 2. 调试模式

启动 OTel Collector 时启用调试日志：
```bash
# 在 docker-compose.yml 中添加环境变量
environment:
  - OTEL_LOG_LEVEL=debug
```

### 3. 验证目标可达性

手动测试指标端点：
```bash
# Spring Boot 应用
curl http://localhost:8089/actuator/prometheus

# cAdvisor
curl http://localhost:8080/metrics
```

## 注意事项

### 1. 多副本部署

Prometheus receiver 是有状态的，多副本会导致重复抓取。解决方案：
- 手动分片：不同副本配置不同的 job
- 使用 Target Allocator（Kubernetes 环境）

### 2. 环境变量转义

Prometheus 配置中的 `$` 会被解释为环境变量，如需保留请使用 `$$` 转义：
```yaml
static_configs:
  - targets: ['localhost:$${PORT}']  # 实际输出: localhost:${PORT}
```

### 3. 不支持的配置

以下 Prometheus 配置不被支持：
- `alert_config`
- `remote_read`
- `remote_write`
- `rule_files`

### 4. 端口冲突

确保以下端口未被占用：
- 21891 - Data Prepper metrics 接收端口
- 8888 - OTel Collector 自身指标端口

## 参考文档

- [Prometheus Receiver 官方文档](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/receiver/prometheusreceiver)
- [Prometheus 配置文档](https://prometheus.io/docs/prometheus/latest/configuration/configuration/)
- [Data Prepper Metrics 文档](https://opensearch.org/docs/latest/data-prepper/)
- [OpenTelemetry Collector 文档](https://opentelemetry.io/docs/collector/)

## 更新记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-03-30 | 1.0 | 初始配置，支持 5 个抓取目标 |
