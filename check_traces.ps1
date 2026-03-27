$body = @{
    size = 1
    query = @{
        match_all = @{}
    }
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri 'http://localhost:9200/otel-v1-apm-span-2026.03.27/_search?pretty' -Method Post -ContentType 'application/json' -Body $body
$response | ConvertTo-Json -Depth 5