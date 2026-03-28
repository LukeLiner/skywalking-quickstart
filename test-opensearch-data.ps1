
# PowerShell Script to Test OpenSearch Data Collection for Trace, Log, and Metric Data
# This script verifies that data is being properly collected and stored in OpenSearch

param(
    [string]$OpenSearchHost = "http://localhost:9200",
    [int]$TimeoutSeconds = 30,
    [int]$RetryCount = 3,
    [int]$RetryDelaySeconds = 5
)

# Set console encoding to UTF-8 to prevent乱码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=========================================" -ForegroundColor Green
Write-Host "OpenSearch Data Collection Test Script" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Testing connection to OpenSearch at: $OpenSearchHost" -ForegroundColor Yellow

# Function to test OpenSearch connectivity
function Test-OpenSearchConnection {
    param([string]$HostUrl)
    
    try {
        $response = Invoke-RestMethod -Uri "$HostUrl/_cluster/health" -Method Get -TimeoutSec $TimeoutSeconds
        if ($response.status -eq "green" -or $response.status -eq "yellow") {
            Write-Host "[PASS] OpenSearch cluster health: $($response.status)" -ForegroundColor Green
            return $true
        } else {
            Write-Host "[FAIL] OpenSearch cluster health: $($response.status)" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "[FAIL] Failed to connect to OpenSearch: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Function to check if index exists
function Test-IndexExists {
    param([string]$HostUrl, [string]$IndexName)
    
    try {
        $response = Invoke-RestMethod -Uri "$HostUrl/$IndexName/_search" -Method Post -TimeoutSec $TimeoutSeconds -ContentType 'application/json' -Body '{"size": 1, "query": {"match_all": {}}}'
        return $true
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -eq 404) {
            return $false
        } else {
            Write-Host "Error checking index $IndexName : $($_.Exception.Message)" -ForegroundColor Yellow
            return $false
        }
    }
}

# Function to query index with retry logic
function Query-IndexWithRetry {
    param([string]$HostUrl, [string]$IndexName, [hashtable]$QueryBody)
    
    $retry = 0
    do {
        try {
            $jsonBody = $QueryBody | ConvertTo-Json -Depth 10
            $response = Invoke-RestMethod -Uri "$HostUrl/$IndexName/_search" -Method Post -TimeoutSec $TimeoutSeconds -ContentType 'application/json' -Body $jsonBody
            return $response
        } catch {
            $retry++
            if ($retry -lt $RetryCount) {
                Write-Host "Attempt $retry failed for index $IndexName, retrying in $RetryDelaySeconds seconds..." -ForegroundColor Yellow
                Start-Sleep -Seconds $RetryDelaySeconds
            } else {
                Write-Host "Failed to query index $IndexName after $RetryCount attempts: $($_.Exception.Message)" -ForegroundColor Red
                return $null
            }
        }
    } while ($retry -lt $RetryCount)
}

# Function to test trace data
function Test-TraceData {
    param([string]$HostUrl)
    
    Write-Host "`n--- Testing Trace Data ---" -ForegroundColor Cyan
    
    # Check for trace indices
    $traceIndices = @("otel-v1-apm-span-*", "otel-v1-apm-span-000001")
    $foundTraces = $false
    
    foreach ($index in $traceIndices) {
        Write-Host "Checking index: $index" -ForegroundColor Gray
        
        $query = @{
            size = 1
            query = @{ match_all = @{} }
        }
        
        $response = Query-IndexWithRetry -HostUrl $HostUrl -IndexName $index -QueryBody $query
        
        if ($response -and $response.hits.total.value -gt 0) {
            Write-Host "[PASS] Found trace data in index: $index" -ForegroundColor Green
            Write-Host "  Total traces: $($response.hits.total.value)" -ForegroundColor Green
            
            # Show sample trace data
            if ($response.hits.hits.Count -gt 0) {
                $sampleTrace = $response.hits.hits[0]._source
                Write-Host "  Sample trace ID: $($sampleTrace.traceId)" -ForegroundColor Green
                Write-Host "  Service name: $($sampleTrace.serviceName)" -ForegroundColor Green
                Write-Host "  Span name: $($sampleTrace.name)" -ForegroundColor Green
            }
            
            $foundTraces = $true
            break
        } elseif ($response) {
            Write-Host "  No trace data found in index: $index (total: $($response.hits.total.value))" -ForegroundColor Yellow
        }
    }
    
    if (-not $foundTraces) {
        Write-Host "[FAIL] No trace data found in any trace indices" -ForegroundColor Red
        Write-Host "  Expected indices: $($traceIndices -join ', ')" -ForegroundColor Red
    }
    
    return $foundTraces
}

# Function to test log data
function Test-LogData {
    param([string]$HostUrl)
    
    Write-Host "`n--- Testing Log Data ---" -ForegroundColor Cyan
    
    # Check for log indices
    $logIndices = @("logs-otel-*")
    $foundLogs = $false
    
    foreach ($index in $logIndices) {
        Write-Host "Checking index: $index" -ForegroundColor Gray
        
        $query = @{
            size = 1
            query = @{ match_all = @{} }
        }
        
        $response = Query-IndexWithRetry -HostUrl $HostUrl -IndexName $index -QueryBody $query
        
        if ($response -and $response.hits.total.value -gt 0) {
            Write-Host "[PASS] Found log data in index: $index" -ForegroundColor Green
            Write-Host "  Total logs: $($response.hits.total.value)" -ForegroundColor Green
            
            # Show sample log data
            if ($response.hits.hits.Count -gt 0) {
                $sampleLog = $response.hits.hits[0]._source
                Write-Host "  Sample log timestamp: $($sampleLog.timestamp)" -ForegroundColor Green
                Write-Host "  Service name: $($sampleLog.service.name)" -ForegroundColor Green
                Write-Host "  Log level: $($sampleLog['log.level'])" -ForegroundColor Green
            }
            
            $foundLogs = $true
            break
        } elseif ($response) {
            Write-Host "  No log data found in index: $index (total: $($response.hits.total.value))" -ForegroundColor Yellow
        }
    }
    
    if (-not $foundLogs) {
        Write-Host "[FAIL] No log data found in any log indices" -ForegroundColor Red
        Write-Host "  Expected indices: $($logIndices -join ', ')" -ForegroundColor Red
    }
    
    return $foundLogs
}

# Function to test metric data
function Test-MetricData {
    param([string]$HostUrl)
    
    Write-Host "`n--- Testing Metric Data ---" -ForegroundColor Cyan
    
    # Check for metric indices
    $metricIndices = @("metrics-otel-*")
    $foundMetrics = $false
    
    foreach ($index in $metricIndices) {
        Write-Host "Checking index: $index" -ForegroundColor Gray
        
        $query = @{
            size = 1
            query = @{ match_all = @{} }
        }
        
        $response = Query-IndexWithRetry -HostUrl $HostUrl -IndexName $index -QueryBody $query
        
        if ($response -and $response.hits.total.value -gt 0) {
            Write-Host "[PASS] Found metric data in index: $index" -ForegroundColor Green
            Write-Host "  Total metrics: $($response.hits.total.value)" -ForegroundColor Green
            
            # Show sample metric data
            if ($response.hits.hits.Count -gt 0) {
                $sampleMetric = $response.hits.hits[0]._source
                Write-Host "  Sample metric name: $($sampleMetric.name)" -ForegroundColor Green
                Write-Host "  Service name: $($sampleMetric.resource.attributes.'service.name')" -ForegroundColor Green
            }
            
            $foundMetrics = $true
            break
        } elseif ($response) {
            Write-Host "  No metric data found in index: $index (total: $($response.hits.total.value))" -ForegroundColor Yellow
        }
    }
    
    if (-not $foundMetrics) {
        Write-Host "[FAIL] No metric data found in any metric indices" -ForegroundColor Red
        Write-Host "  Expected indices: $($metricIndices -join ', ')" -ForegroundColor Red
    }
    
    return $foundMetrics
}

# Function to generate traffic to trigger data collection
function Generate-Traffic {
    Write-Host "`n--- Generating Traffic to Trigger Data Collection ---" -ForegroundColor Cyan
    
    Write-Host "Generating traffic to services to ensure data collection..." -ForegroundColor Yellow
    
    # Try to reach the microservices to generate traces
    $services = @(
        @{ name = "xiaozhou-order"; url = "http://localhost:8089/actuator/health" },
        @{ name = "xiaozhou-product"; url = "http://localhost:8090/actuator/health" },
        @{ name = "xiaozhou-stock"; url = "http://localhost:8091/actuator/health" }
    )
    
    foreach ($service in $services) {
        try {
            $response = Invoke-RestMethod -Uri $service.url -Method Get -TimeoutSec 10
            Write-Host "[SUCCESS] Successfully contacted $($service.name)" -ForegroundColor Green
        } catch {
            Write-Host "[ERROR] Failed to contact $($service.name): $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
    
    Write-Host "Waiting 10 seconds for data to be indexed..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
}

# Main execution
$connectionOk = Test-OpenSearchConnection -HostUrl $OpenSearchHost

if ($connectionOk) {
    # Generate some traffic to ensure data is flowing
    Generate-Traffic
    
    # Test each data type
    $tracesOk = Test-TraceData -HostUrl $OpenSearchHost
    $logsOk = Test-LogData -HostUrl $OpenSearchHost
    $metricsOk = Test-MetricData -HostUrl $OpenSearchHost
    
    # Summary
    Write-Host "`n=========================================" -ForegroundColor Green
    Write-Host "Test Results Summary:" -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host "Traces:  $(if($tracesOk) {'[PASS]'} else {'[FAIL]'})" -ForegroundColor $(if($tracesOk) {'Green'} else {'Red'})
    Write-Host "Logs:    $(if($logsOk) {'[PASS]'} else {'[FAIL]'})" -ForegroundColor $(if($logsOk) {'Green'} else {'Red'})
    Write-Host "Metrics: $(if($metricsOk) {'[PASS]'} else {'[FAIL]'})" -ForegroundColor $(if($metricsOk) {'Green'} else {'Red'})
    
    if ($tracesOk -and $logsOk -and $metricsOk) {
        Write-Host "`n[SUCCESS] All data types are being collected and stored properly!" -ForegroundColor Green
        Write-Host "OpenSearch is successfully receiving traces, logs, and metrics." -ForegroundColor Green
    } else {
        Write-Host "`n[WARNING] Some data types are missing or not being collected properly." -ForegroundColor Yellow
        Write-Host "Please check your OpenTelemetry collector and Data Prepper configurations." -ForegroundColor Yellow
    }
} else {
    Write-Host "`n[ERROR] Cannot connect to OpenSearch. Please verify that OpenSearch is running." -ForegroundColor Red
}

Write-Host "`nTest completed." -ForegroundColor Green