$body = '{"size": 1, "query": {"match_all": {}}}'
Invoke-RestMethod -Uri 'http://localhost:9200/otel-v1-apm-span-000001/_search?pretty' -Method Post -ContentType 'application/json' -Body $body