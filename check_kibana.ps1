$body = @{
    query = @{
        match_all = @{}
    }
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri 'http://localhost:9200/.kibana/_search?pretty' -Method Post -ContentType 'application/json' -Body $body
$response | ConvertTo-Json -Depth 5
