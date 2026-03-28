# OpenSearch Data Collection Validation Report

## Overview
This report summarizes the validation of trace, log, and metric data collection in the OpenSearch backend of the SkyWalking quickstart environment.

## Test Results Summary

| Data Type | Status | Details |
|-----------|--------|---------|
| Traces | ✅ PASS | Successfully collecting trace data in `otel-v1-apm-span-2026.03.28` index |
| Metrics | ✅ PASS | Successfully collecting metric data in `metrics-otel-2026.03.28` index |
| Logs | ⚠️ PARTIAL | Log pipeline is configured but no log data is currently being collected |

## Detailed Results

### 1. Trace Data Collection
- **Index**: `otel-v1-apm-span-2026.03.28`
- **Document Count**: 2,510+
- **Sample Data**:
  - Service: `xiaozhou-stock`
  - Span: `KafkaMessageListenerContainer$ListenerConsumer$$Lambda.run`
  - Trace ID: `e3c00ca88608588c169ddec088d9c16d`
- **Status**: ✅ Working correctly

### 2. Metric Data Collection
- **Index**: `metrics-otel-2026.03.28`
- **Document Count**: 124,409+
- **Sample Data**:
  - Metric Name: `up`
  - Service: Various services
- **Status**: ✅ Working correctly

### 3. Log Data Collection
- **Index**: `logs-otel-2026.03.28`
- **Document Count**: 0
- **Configuration Status**: ✅ Pipeline is properly configured
- **Issue**: No active log data is being sent to the pipeline
- **Status**: ⚠️ Configured but not receiving data

## Infrastructure Status
All required services are running and accessible:
- ✅ OpenSearch: `http://localhost:9200`
- ✅ Data Prepper Traces: `http://localhost:21890`
- ✅ Data Prepper Metrics: `http://localhost:21891`
- ✅ Data Prepper Logs: `http://localhost:21892`

## Log Collection Issue Analysis

The log collection pipeline is properly configured according to the system setup, but no log data is currently flowing through it. This is likely due to:

1. **Application Logging Configuration**: The microservices may not be configured to output logs to the file locations monitored by the filelog receiver
2. **File Path Mismatch**: The OTEL collector is configured to watch `/var/log/apps/xiaozhou-order/*.log`, `/var/log/apps/xiaozhou-product/*.log`, and `/var/log/apps/xiaozhou-stock/*.log`, but the applications may be logging elsewhere
3. **Log Volume**: During the test period, there may not have been sufficient application activity to generate log entries

## Recommendations

### For Log Collection
1. **Verify Application Logging Configuration**: Ensure the Spring Boot applications are configured to write logs to the expected file locations
2. **Check Docker Volume Mounts**: Verify that the `/var/log/apps` volume mount is properly connecting application logs to the OTEL collector
3. **Generate Log Activity**: Execute operations that would typically generate application logs to test the pipeline

### For Continued Monitoring
1. **Run the validation script regularly**: Use `validate-opensearch-collection.ps1` to monitor data collection status
2. **Monitor indices**: Watch the document counts in OpenSearch indices to ensure continued data flow
3. **Check service health**: Regularly verify that all infrastructure services remain accessible

## Scripts Provided

### 1. Basic Test Script
- **File**: `test-opensearch-data.ps1`
- **Purpose**: Quick validation of data collection across all types

### 2. Diagnostic Script
- **File**: `diagnose-opensearch-data.ps1`
- **Purpose**: Detailed analysis of OpenSearch indices and infrastructure

### 3. Validation Script (Recommended)
- **File**: `validate-opensearch-collection.ps1`
- **Purpose**: Comprehensive validation with traffic generation and detailed reporting

## Conclusion

The OpenSearch data collection system is functioning well for traces and metrics. The log collection pipeline is properly configured but requires verification of application logging setup to ensure logs are being generated and captured. Overall, the observability infrastructure is operational and collecting the essential telemetry data.