$body = @{
    attributes = @{
        title = "otel-v1-apm-span-*"
        timeFieldName = "startTime"
    }
} | ConvertTo-Json -Depth 3

$headers = @{
    "osd-xsrf" = "true"
}

$response = Invoke-WebRequest -Uri "http://localhost:5601/api/saved_objects/index-pattern" -Method POST -ContentType "application/json" -Body $body -Headers $headers -UseBasicParsing
$response.Content
