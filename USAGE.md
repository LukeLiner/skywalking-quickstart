# OpenSearch Data Collection Validation Scripts

This repository contains PowerShell scripts to validate that trace, log, and metric data are being properly collected and stored in OpenSearch.

## Scripts Included

### 1. `validate-opensearch-collection.ps1` (Recommended)
Comprehensive validation script that:
- Tests connectivity to OpenSearch
- Validates infrastructure services
- Generates traffic to trigger data collection
- Checks all three data types (traces, logs, metrics)
- Provides detailed results and recommendations

**Usage:**
```powershell
.\validate-opensearch-collection.ps1
```

**Advanced usage:**
```powershell
# With custom OpenSearch host
.\validate-opensearch-collection.ps1 -OpenSearchHost "http://your-host:9200"

# With custom timeout and retry settings
.\validate-opensearch-collection.ps1 -TimeoutSeconds 60 -RetryCount 5 -RetryDelaySeconds 10
```

### 2. `test-opensearch-data.ps1`
Basic script for quick validation of data collection across all types.

**Usage:**
```powershell
.\test-opensearch-data.ps1
```

### 3. `diagnose-opensearch-data.ps1`
Diagnostic script that provides detailed analysis of OpenSearch indices and infrastructure.

**Usage:**
```powershell
.\diagnose-opensearch-data.ps1
```

## Prerequisites

- PowerShell 5.1 or later
- Network access to OpenSearch instance (default: `http://localhost:9200`)
- Access to Data Prepper endpoints (ports 21890, 21891, 21892)
- Access to OpenTelemetry Collector endpoints (ports 4317, 4318)

## Expected Results

### Successful Collection
- **Traces**: Should find data in `otel-v1-apm-span-*` indices
- **Metrics**: Should find data in `metrics-otel-*` indices  
- **Logs**: Should find data in `logs-otel-*` indices

### Common Issues
- **No log data**: Usually indicates application logging configuration issue
- **Service unreachable**: Check Docker containers and network connectivity
- **Index not found**: Verify Data Prepper pipeline configuration

## Troubleshooting

If the scripts report issues:

1. **Check container status**:
   ```bash
   docker-compose ps
   ```

2. **Review container logs**:
   ```bash
   docker-compose logs otel-collector
   docker-compose logs data-prepper
   docker-compose logs opensearch
   ```

3. **Verify Data Prepper pipelines** by checking `data-prepper/pipelines.yaml`

4. **Confirm application logging** is configured to write to monitored paths

## Character Encoding

All scripts now include UTF-8 encoding support to prevent character display issues (乱码) in Windows environments.

## Integration with CI/CD

These scripts can be integrated into automated testing workflows to ensure data collection remains functional:

```powershell
# Example CI/CD usage
$result = .\validate-opensearch-collection.ps1
if ($LastExitCode -ne 0) {
    throw "Data collection validation failed"
}
