# 检查 Metrics 数据
$body = @{
    size = 5
    query = @{
        match_all = @{}
    }
    sort = @(@{ "@timestamp" = @{ order = "desc" } })
} | ConvertTo-Json

Write-Host "=== 查询 Metrics 数据 (otel-v1-apm-metric-*) ===" -ForegroundColor Green

try {
    $response = Invoke-RestMethod -Uri 'http://localhost:9200/otel-v1-apm-metric-*/_search?pretty' -Method Post -ContentType 'application/json' -Body $body
    Write-Host "命中文档数：$($response.hits.total.value)" -ForegroundColor Yellow
    Write-Host "`n=== 最近 5 条 Metric 数据 ===" -ForegroundColor Green
    $response.hits.hits | ForEach-Object {
        $source = $_._source
        $serviceName = $source.serviceName
        $metricName = $source.metric.name
        $value = $source.metric.value
        $timestamp = $source.timestamp
        $unit = $source.metric.unit
        Write-Host "[$timestamp] Service: $serviceName" -ForegroundColor Cyan
        Write-Host "  Metric: $metricName = $value ($unit)" -ForegroundColor White
        Write-Host ""
    }
} catch {
    Write-Host "未找到 Metrics 数据或查询失败" -ForegroundColor Red
    Write-Host "错误：$_" -ForegroundColor Red
}