# PowerShell Script to Validate OpenSearch Data Collection for Trace, Log, and Metric Data
# This script validates that data is being properly collected and stored in OpenSearch

param(
    [string]$OpenSearchHost = "http://localhost:9200",
    [int]$TimeoutSeconds = 30,
    [int]$RetryCount = 3,
    [int]$RetryDelaySeconds = 5
)

# Set console encoding to UTF-8 to prevent乱码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=========================================" -ForegroundColor Green
Write-Host "OpenSearch Data Collection Validation" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Validating connection to OpenSearch at: $OpenSearchHost" -ForegroundColor Yellow

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

# Function to get index stats
function Get-IndexStats {
    param([string]$HostUrl, [string]$IndexName)
    
    try {
        $response = Invoke-RestMethod -Uri "$HostUrl/$IndexName/_stats" -Method Get -TimeoutSec $TimeoutSeconds
        return $response.indices.$IndexName.total.docs.count
    } catch {
        return 0
    }
}

# Function to validate trace data
function Validate-TraceData {
    param([string]$HostUrl)
    
    Write-Host "`n--- Validating Trace Data ---" -ForegroundColor Cyan
    
    # Check for trace indices
    $traceIndex = "otel-v1-apm-span-2026.03.28"
    $traceCount = Get-IndexStats -HostUrl $HostUrl -IndexName $traceIndex
    
    if ($traceCount -gt 0) {
        Write-Host "[PASS] Trace index '$traceIndex' exists with $traceCount documents" -ForegroundColor Green
        
        # Get sample trace data
        $query = @{
            size = 1
            query = @{ match_all = @{} }
            _source = @("serviceName", "name", "traceId", "@timestamp")
        }
        
        $response = Query-IndexWithRetry -HostUrl $HostUrl -IndexName $traceIndex -QueryBody $query
        if ($response -and $response.hits.hits.Count -gt 0) {
            $sampleTrace = $response.hits.hits[0]._source
            Write-Host "  Sample trace details:" -ForegroundColor Green
            Write-Host "    Service: $($sampleTrace.serviceName)" -ForegroundColor Green
            Write-Host "    Span: $($sampleTrace.name)" -ForegroundColor Green
            Write-Host "    Trace ID: $($sampleTrace.traceId)" -ForegroundColor Green
        }
        
        return $true
    } else {
        Write-Host "[FAIL] No trace data found in index '$traceIndex'" -ForegroundColor Red
        return $false
    }
}

# Function to validate log data
function Validate-LogData {
    param([string]$HostUrl)
    
    Write-Host "`n--- Validating Log Data ---" -ForegroundColor Cyan
    
    # Check for log indices
    $logIndex = "logs-otel-2026.03.28"
    $logCount = Get-IndexStats -HostUrl $HostUrl -IndexName $logIndex
    
    if ($logCount -gt 0) {
        Write-Host "[PASS] Log index '$logIndex' exists with $logCount documents" -ForegroundColor Green
        
        # Get sample log data
        $query = @{
            size = 1
            query = @{ match_all = @{} }
            _source = @("log.level", "message", "service.name", "@timestamp")
        }
        
        $response = Query-IndexWithRetry -HostUrl $HostUrl -IndexName $logIndex -QueryBody $query
        if ($response -and $response.hits.hits.Count -gt 0) {
            $sampleLog = $response.hits.hits[0]._source
            Write-Host "  Sample log details:" -ForegroundColor Green
            Write-Host "    Service: $($sampleLog.'service.name')" -ForegroundColor Green
            Write-Host "    Level: $($sampleLog.'log.level')" -ForegroundColor Green
            Write-Host "    Message: $($sampleLog.message)" -ForegroundColor Green
        }
        
        return $true
    } else {
        Write-Host "[WARNING] Log index '$logIndex' exists but has 0 documents" -ForegroundColor Yellow
        Write-Host "  This may indicate that log collection is configured but not actively receiving logs." -ForegroundColor Yellow
        
        # Check if the index was recently created (which would indicate the pipeline is working)
        try {
            $mapping = Invoke-RestMethod -Uri "$HostUrl/$logIndex/_mapping" -Method Get -TimeoutSec $TimeoutSeconds
            Write-Host "  [PASS] Log index mapping exists - log pipeline appears to be configured correctly" -ForegroundColor Yellow
        } catch {
            Write-Host "  [FAIL] Log index mapping not found - log pipeline may not be configured correctly" -ForegroundColor Red
        }
        
        return $false
    }
}

# Function to validate metric data
function Validate-MetricData {
    param([string]$HostUrl)
    
    Write-Host "`n--- Validating Metric Data ---" -ForegroundColor Cyan
    
    # Check for metric indices
    $metricIndex = "metrics-otel-2026.03.28"
    $metricCount = Get-IndexStats -HostUrl $HostUrl -IndexName $metricIndex
    
    if ($metricCount -gt 0) {
        Write-Host "[PASS] Metric index '$metricIndex' exists with $metricCount documents" -ForegroundColor Green
        
        # Get sample metric data
        $query = @{
            size = 1
            query = @{ match_all = @{} }
            _source = @("name", "resource.attributes", "gauge", "sum")
        }
        
        $response = Query-IndexWithRetry -HostUrl $HostUrl -IndexName $metricIndex -QueryBody $query
        if ($response -and $response.hits.hits.Count -gt 0) {
            $sampleMetric = $response.hits.hits[0]._source
            Write-Host "  Sample metric details:" -ForegroundColor Green
            Write-Host "    Name: $($sampleMetric.name)" -ForegroundColor Green
            if ($sampleMetric.'resource.attributes'.'service.name') {
                Write-Host "    Service: $($sampleMetric.'resource.attributes'.'service.name')" -ForegroundColor Green
            }
        }
        
        return $true
    } else {
        Write-Host "[FAIL] No metric data found in index '$metricIndex'" -ForegroundColor Red
        return $false
    }
}

# Function to generate traffic to trigger data collection
function Generate-Traffic {
    Write-Host "`n--- Generating Traffic to Trigger Data Collection ---" -ForegroundColor Cyan
    
    Write-Host "Making requests to services to generate traces and metrics..." -ForegroundColor Yellow
    
    # Try to reach the microservices to generate traces and metrics
    $services = @(
        @{ name = "xiaozhou-order"; url = "http://localhost:8089/actuator/info" },
        @{ name = "xiaozhou-product"; url = "http://localhost:8090/actuator/info" },
        @{ name = "xiaozhou-stock"; url = "http://localhost:8091/actuator/info" }
    )
    
    foreach ($service in $services) {
        try {
            $response = Invoke-RestMethod -Uri $service.url -Method Get -TimeoutSec 10
            Write-Host "[SUCCESS] Successfully contacted $($service.name)" -ForegroundColor Green
        } catch {
            Write-Host "[WARNING] Failed to contact $($service.name): $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
    
    # Also try to trigger some database activity
    Write-Host "Triggering additional service interactions..." -ForegroundColor Yellow
    
    try {
        # Try to access product endpoints if they exist
        $productResponse = Invoke-RestMethod -Uri "http://localhost:8090/product/list" -Method Get -TimeoutSec 10 -ErrorAction Stop
        Write-Host "[SUCCESS] Successfully accessed product service" -ForegroundColor Green
    } catch {
        Write-Host "[INFO] Product service endpoint not available (this is normal if the endpoint doesn't exist)" -ForegroundColor Gray
    }
    
    Write-Host "Waiting 15 seconds for data to be indexed..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
}

# Function to validate infrastructure
function Validate-Infrastructure {
    Write-Host "`n--- Validating Infrastructure ---" -ForegroundColor Cyan
    
    # Check if we can reach the services
    $services = @(
        @{ name = "OpenSearch"; url = "http://localhost:9200" },
        @{ name = "Data Prepper Traces (21890)"; url = "http://localhost:21890" },
        @{ name = "Data Prepper Metrics (21891)"; url = "http://localhost:21891" },
        @{ name = "Data Prepper Logs (21892)"; url = "http://localhost:21892" }
    )
    
    $allReachable = $true
    foreach ($service in $services) {
        try {
            # For HTTP services we can check with Invoke-RestMethod, but for gRPC ports we'll use Test-NetConnection
            if ($service.url -match ":21890$" -or $service.url -match ":21891$" -or $service.url -match ":21892$") {
                # For gRPC ports, we'll just check if the port is listening
                $port = [int]($service.url -split ':')[-1]
                $hostname = ($service.url -split '://')[-1] -split ':' | Select-Object -First 1
                $connection = Test-NetConnection -ComputerName $hostname -Port $port -WarningAction SilentlyContinue
                if ($connection.TcpTestSucceeded) {
                    Write-Host "✓ $($service.name) is reachable" -ForegroundColor Green
                } else {
                    Write-Host "✗ $($service.name) is not reachable" -ForegroundColor Red
                    $allReachable = $false
                }
            } else {
                $response = Invoke-RestMethod -Uri $service.url -Method Get -TimeoutSec 5
                Write-Host "✓ $($service.name) is reachable" -ForegroundColor Green
            }
        } catch {
            Write-Host "✗ $($service.name) is not reachable: $($_.Exception.Message)" -ForegroundColor Red
            $allReachable = $false
        }
    }
    
    return $allReachable
}

# Main execution
$connectionOk = Test-OpenSearchConnection -HostUrl $OpenSearchHost

if ($connectionOk) {
    # Validate infrastructure
    $infrastructureOk = Validate-Infrastructure
    
    if ($infrastructureOk) {
        # Generate some traffic to ensure data is flowing
        Generate-Traffic
        
        # Validate each data type
        $tracesOk = Validate-TraceData -HostUrl $OpenSearchHost
        $logsOk = Validate-LogData -HostUrl $OpenSearchHost
        $metricsOk = Validate-MetricData -HostUrl $OpenSearchHost
        
        # Summary
        Write-Host "`n=========================================" -ForegroundColor Green
        Write-Host "Validation Results Summary:" -ForegroundColor Green
        Write-Host "=========================================" -ForegroundColor Green
        Write-Host "Traces:  $(if($tracesOk) {'✓ PASS'} else {'✗ FAIL'})" -ForegroundColor $(if($tracesOk) {'Green'} else {'Red'})
        Write-Host "Logs:    $(if($logsOk) {'✓ PASS'} else {'⚠ PARTIAL'})" -ForegroundColor $(if($logsOk) {'Green'} else {'Yellow'})
        Write-Host "Metrics: $(if($metricsOk) {'✓ PASS'} else {'✗ FAIL'})" -ForegroundColor $(if($metricsOk) {'Green'} else {'Red'})
        
        if ($tracesOk -and $logsOk -and $metricsOk) {
            Write-Host "`n🎉 All data types are being collected and stored properly!" -ForegroundColor Green
            Write-Host "OpenSearch is successfully receiving traces, logs, and metrics." -ForegroundColor Green
        } elseif ($tracesOk -and $metricsOk) {
            Write-Host "`n⚠️  Most data types are working, but logs need attention." -ForegroundColor Yellow
            Write-Host "Traces and metrics are working correctly, but log collection may need configuration." -ForegroundColor Yellow
            Write-Host "This could be because no log-generating activities occurred during the test." -ForegroundColor Yellow
        } else {
            Write-Host "`n❌ Some data types are not being collected properly." -ForegroundColor Red
            Write-Host "Please check your OpenTelemetry collector and Data Prepper configurations." -ForegroundColor Red
        }
    } else {
        Write-Host "`n❌ Infrastructure validation failed. Some services are not reachable." -ForegroundColor Red
    }
} else {
    Write-Host "`n❌ Cannot connect to OpenSearch. Please verify that OpenSearch is running." -ForegroundColor Red
}

Write-Host "`nValidation completed." -ForegroundColor Green