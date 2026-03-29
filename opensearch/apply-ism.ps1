# Apply ISM Policy for 24h Rollover
# Run this script after OpenSearch is running

$ErrorActionPreference = "Stop"

$opensearchUrl = "http://localhost:9200"
$indexName = "otel-v1-apm-span-000001"
$policyFile = "$PSScriptRoot\ism-raw-span-policy.json"
$templateFile = "$PSScriptRoot\ism-index-template.json"

Write-Host "=== Applying ISM Policy for 24h Rollover ===" -ForegroundColor Cyan

# 1. Update existing index to add rollover_alias setting
Write-Host "`n[1/4] Updating index settings for $indexName..." -ForegroundColor Yellow
$settingsJson = @{
    "index.plugins.index_state_management.rollover_alias" = "otel-v1-apm-span"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$opensearchUrl/$indexName/_settings" `
        -Method PUT `
        -ContentType "application/json" `
        -Body $settingsJson
    Write-Host "  ✓ Index settings updated" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to update index settings: $_" -ForegroundColor Red
}

# 2. Create index template
Write-Host "`n[2/4] Creating index template..." -ForegroundColor Yellow
try {
    $templateContent = Get-Content $templateFile -Raw
    $response = Invoke-RestMethod -Uri "$opensearchUrl/_template/otel-v1-apm-span-template" `
        -Method PUT `
        -ContentType "application/json" `
        -Body $templateContent
    Write-Host "  ✓ Index template created" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to create index template: $_" -ForegroundColor Red
}

# 3. Create ISM policy
Write-Host "`n[3/4] Creating ISM policy..." -ForegroundColor Yellow
try {
    $policyContent = Get-Content $policyFile -Raw
    $response = Invoke-RestMethod -Uri "$opensearchUrl/_plugins/_ism/policies/raw-span-24h-policy" `
        -Method PUT `
        -ContentType "application/json" `
        -Body $policyContent
    Write-Host "  ✓ ISM policy created" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to create ISM policy: $_" -ForegroundColor Red
}

# 4. Apply policy to existing index
Write-Host "`n[4/4] Applying policy to existing index..." -ForegroundColor Yellow
$applyBody = @{
    indices = @($indexName)
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$opensearchUrl/_plugins/_ism/policies/raw-span-24h-policy/_apply" `
        -Method POST `
        -ContentType "application/json" `
        -Body $applyBody
    Write-Host "  ✓ Policy applied to $indexName" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to apply policy: $_" -ForegroundColor Red
}

Write-Host "`n=== Done! ===" -ForegroundColor Cyan
Write-Host "The index will rollover every 24 hours."
Write-Host "Indices older than 30 days will be automatically deleted."