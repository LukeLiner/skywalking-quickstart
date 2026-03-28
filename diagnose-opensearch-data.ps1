# PowerShell Script to Diagnose OpenSearch Data Collection Issues
# This script provides detailed diagnostics for trace, log, and metric data collection

param(
    [string]$OpenSearchHost = "http://localhost:9200",
    [int]$TimeoutSeconds = 30
)

# Set console encoding to UTF-8 to prevent乱码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=========================================" -ForegroundColor Green
Write-Host "OpenSearch Data Collection Diagnosis" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""

# Function to test OpenSearch connectivity
function Test-OpenSearchConnection {
    param([string]$HostUrl)
    
    try {
        $response = Invoke-RestMethod -Uri "$HostUrl/_cluster/health" -Method Get -TimeoutSec $TimeoutSeconds
        Write-Host "✓ OpenSearch cluster health: $($response.status)" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "✗ Failed to connect to OpenSearch: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Function to list all indices
function Get-AllIndices {
    param([string]$HostUrl)
    
    try {
        $response = Invoke-RestMethod -Uri "$HostUrl/_cat/indices?v" -Method Get -TimeoutSec $TimeoutSeconds
        Write-Host "`n--- All OpenSearch Indices ---" -ForegroundColor Cyan
        $response | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
        return $response
    } catch {
        Write-Host "✗ Failed to get indices: $($_.Exception.Message)" -ForegroundColor Red
        return @()
    }
}

# Function to check specific index
function Get-IndexInfo {
    param([string]$HostUrl, [string]$IndexName)
    
    try {
        $response = Invoke-RestMethod -Uri "$HostUrl/$IndexName/_stats" -Method Get -TimeoutSec $TimeoutSeconds
        $docsCount = $response.indices.$IndexName.total.docs.count
        $storeSize = $response.indices.$IndexName.total.store.size
        Write-Host "  Index: $IndexName" -ForegroundColor White
        Write-Host "    Documents: $docsCount" -ForegroundColor White
        Write-Host "    Store Size: $storeSize" -ForegroundColor White
        return $docsCount
    } catch {
        Write-Host "  Index: $IndexName - Not Found" -ForegroundColor Red
        return 0
    }
}

# Function to test log collection specifically
function Test-LogCollection {
    param([string]$HostUrl)
    
    Write-Host "`n--- Detailed Log Collection Analysis ---" -ForegroundColor Cyan
    
    # Check for any log-related indices
    $allIndices = Get-AllIndices -HostUrl $HostUrl
    $logIndices = $allIndices | Where-Object { $_ -like "*log*" -or $_ -like "*logs*" }
    
    if ($logIndices) {
        Write-Host "`nFound potential log indices:" -ForegroundColor Yellow
        $logIndices | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
    } else {
        Write-Host "`nNo log-related indices found." -ForegroundColor Red
    }
    
    # Check for common log index patterns
    $commonLogPatterns = @(
        "logs-otel-*",
        "logs-*",
        "app-logs-*",
        "filebeat-*",
        "*-log-*"
    )
    
    Write-Host "`nChecking for common log index patterns:" -ForegroundColor Cyan
    foreach ($pattern in $commonLogPatterns) {
        try {
            $response = Invoke-RestMethod -Uri "$HostUrl/_cat/indices/$pattern?v" -Method Get -TimeoutSec $TimeoutSeconds
            if ($response) {
                Write-Host "  Found indices matching '$pattern':" -ForegroundColor Green
                $response | ForEach-Object { Write-Host "    $_" -ForegroundColor Green }
            } else {
                Write-Host "  No indices found for pattern: $pattern" -ForegroundColor Gray
            }
        } catch {
            # Pattern might not match any indices, which is OK
            Write-Host "  No indices found for pattern: $pattern" -ForegroundColor Gray
        }
    }
}

# Function to test trace collection specifically
function Test-TraceCollection {
    param([string]$HostUrl)
    
    Write-Host "`n--- Detailed Trace Collection Analysis ---" -ForegroundColor Cyan
    
    # Check for trace-related indices
    $tracePatterns = @("otel-v1-apm-span*", "traces-*", "*-span-*", "jaeger-*")
    
    foreach ($pattern in $tracePatterns) {
        try {
            $response = Invoke-RestMethod -Uri "$HostUrl/_cat/indices/$pattern?v" -Method Get -TimeoutSec $TimeoutSeconds
            if ($response) {
                Write-Host "Found trace indices matching '$pattern':" -ForegroundColor Green
                $response | ForEach-Object { 
                    $parts = $_ -split '\s+'
                    if ($parts.Length -ge 3) {
                        Write-Host "  Index: $($parts[2]), Docs: $($parts[6])" -ForegroundColor Green
                    }
                }
                
                # Get sample trace data
                $matchingIndices = $response | ForEach-Object { ($_ -split '\s+')[2] }
                foreach ($idx in $matchingIndices) {
                    if ($idx -match "otel-v1-apm-span") {
                        try {
                            $sampleQuery = @{
                                size = 1
                                query = @{ match_all = @{} }
                                _source = @("serviceName", "name", "traceId", "@timestamp")
                            } | ConvertTo-Json -Depth 10
                            
                            $sampleResponse = Invoke-RestMethod -Uri "$HostUrl/$idx/_search" -Method Post -TimeoutSec $TimeoutSeconds -ContentType 'application/json' -Body $sampleQuery
                            if ($sampleResponse.hits.hits.Count -gt 0) {
                                $hit = $sampleResponse.hits.hits[0]
                                Write-Host "  Sample trace from $($idx):" -ForegroundColor Green
                                Write-Host "    Service: $($hit._source.serviceName)" -ForegroundColor Green
                                Write-Host "    Span: $($hit._source.name)" -ForegroundColor Green
                                Write-Host "    Trace ID: $($hit._source.traceId)" -ForegroundColor Green
                            }
                        } catch {
                            Write-Host "  Could not fetch sample data from $idx" -ForegroundColor Yellow
                        }
                    }
                }
                break
            }
        } catch {
            # Pattern might not match any indices, which is OK
        }
    }
}

# Function to test metric collection specifically
function Test-MetricCollection {
    param([string]$HostUrl)
    
    Write-Host "`n--- Detailed Metric Collection Analysis ---" -ForegroundColor Cyan
    
    # Check for metric-related indices
    $metricPatterns = @("metrics-*", "otel-metrics*", "*-metric*", "prometheus-*")
    
    foreach ($pattern in $metricPatterns) {
        try {
            $response = Invoke-RestMethod -Uri "$HostUrl/_cat/indices/$pattern?v" -Method Get -TimeoutSec $TimeoutSeconds
            if ($response) {
                Write-Host "Found metric indices matching '$pattern':" -ForegroundColor Green
                $response | ForEach-Object { 
                    $parts = $_ -split '\s+'
                    if ($parts.Length -ge 3) {
                        Write-Host "  Index: $($parts[2]), Docs: $($parts[6])" -ForegroundColor Green
                    }
                }
                
                # Get sample metric data
                $matchingIndices = $response | ForEach-Object { ($_ -split '\s+')[2] }
                foreach ($idx in $matchingIndices) {
                    try {
                        $sampleQuery = @{
                            size = 1
                            query = @{ match_all = @{} }
                            _source = @("name", "resource.attributes", "gauge", "sum")
                        } | ConvertTo-Json -Depth 10
                        
                        $sampleResponse = Invoke-RestMethod -Uri "$HostUrl/$idx/_search" -Method Post -TimeoutSec $TimeoutSeconds -ContentType 'application/json' -Body $sampleQuery
                        if ($sampleResponse.hits.hits.Count -gt 0) {
                            $hit = $sampleResponse.hits.hits[0]
                                Write-Host "  Sample metric from $($idx):" -ForegroundColor Green
                            Write-Host "    Name: $($hit._source.name)" -ForegroundColor Green
                            if ($hit._source.'resource.attributes') {
                                Write-Host "    Service: $($hit._source.'resource.attributes'.'service.name')" -ForegroundColor Green
                            }
                        }
                    } catch {
                        Write-Host "  Could not fetch sample data from $idx" -ForegroundColor Yellow
                    }
                }
                break
            }
        } catch {
            # Pattern might not match any indices, which is OK
        }
    }
}

# Function to check Data Prepper and OTel Collector status
function Test-InfrastructureStatus {
    Write-Host "`n--- Infrastructure Status ---" -ForegroundColor Cyan
    
    # Check if we can reach the services
    $services = @(
        @{ name = "OpenSearch"; url = "http://localhost:9200" },
        @{ name = "Data Prepper Traces (21890)"; url = "http://localhost:21890" },
        @{ name = "Data Prepper Metrics (21891)"; url = "http://localhost:21891" },
        @{ name = "Data Prepper Logs (21892)"; url = "http://localhost:21892" },
        @{ name = "OTel Collector gRPC (4317)"; url = "http://localhost:4317" },
        @{ name = "OTel Collector HTTP (4318)"; url = "http://localhost:4318" }
    )
    
    foreach ($service in $services) {
        try {
            # For HTTP services we can check with Invoke-RestMethod, but for gRPC ports we'll use Test-NetConnection
            if ($service.url -match ":4317$" -or $service.url -match ":21890$" -or $service.url -match ":21891$" -or $service.url -match ":21892$") {
                # For gRPC ports, we'll just check if the port is listening
                $port = [int]($service.url -split ':')[-1]
                $hostname = ($service.url -split '://')[-1] -split ':' | Select-Object -First 1
                $connection = Test-NetConnection -ComputerName $hostname -Port $port -WarningAction SilentlyContinue
                if ($connection.TcpTestSucceeded) {
                    Write-Host "✓ $($service.name) is reachable" -ForegroundColor Green
                } else {
                    Write-Host "✗ $($service.name) is not reachable" -ForegroundColor Red
                }
            } else {
                $response = Invoke-RestMethod -Uri $service.url -Method Get -TimeoutSec 5
                Write-Host "✓ $($service.name) is reachable" -ForegroundColor Green
            }
        } catch {
            Write-Host "✗ $($service.name) is not reachable: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

# Main execution
$connectionOk = Test-OpenSearchConnection -HostUrl $OpenSearchHost

if ($connectionOk) {
    Get-AllIndices -HostUrl $OpenSearchHost
    Test-TraceCollection -HostUrl $OpenSearchHost
    Test-MetricCollection -HostUrl $OpenSearchHost
    Test-LogCollection -HostUrl $OpenSearchHost
    Test-InfrastructureStatus
} else {
    Write-Host "`n❌ Cannot connect to OpenSearch. Please verify that OpenSearch is running." -ForegroundColor Red
}

Write-Host "`nDiagnosis completed." -ForegroundColor Green