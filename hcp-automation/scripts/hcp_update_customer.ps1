param(
    [Parameter(Mandatory = $true)]
    [string]$customerId,

    [Parameter(Mandatory = $true)]
    [string]$firstName,

    [Parameter(Mandatory = $true)]
    [string]$lastName,

    [string]$companyName,
    [string]$mobile,
    [string]$email,
    [string]$displayName,
    [string]$note
)

$ErrorActionPreference = "Stop"

$apiKey = $env:HCP_API_TOKEN
if ([string]::IsNullOrWhiteSpace($apiKey)) {
    throw "HCP_API_TOKEN is missing."
}

$headers = @{
    "Authorization" = "Token $($apiKey)"
    "Content-Type"  = "application/json"
    "Accept"        = "application/json"
}

$body = @{
    first_name = $firstName
    last_name  = $lastName
}

if (-not [string]::IsNullOrWhiteSpace($mobile)) {
    $body.mobile_number = $mobile
}

if (-not [string]::IsNullOrWhiteSpace($email)) {
    $body.email = $email
}

if (-not [string]::IsNullOrWhiteSpace($companyName)) {
    $body.company = $companyName
}

if (-not [string]::IsNullOrWhiteSpace($displayName)) {
    $body.display_name = $displayName
}

if (-not [string]::IsNullOrWhiteSpace($note)) {
    $body.notes = $note
}

$uri = "https://api.housecallpro.com/customers/$customerId"
$jsonBody = $body | ConvertTo-Json
$updated = $false

foreach ($method in @("Patch", "Put")) {
    try {
        Invoke-RestMethod -Uri $uri -Method $method -Headers $headers -Body $jsonBody | Out-Null
        $updated = $true
        break
    }
    catch {
        Write-Host "Customer update attempt with method '$method' failed: $($_.Exception.Message)"
    }
}

if (-not $updated) {
    throw "Customer update failed for customerId '$customerId'."
}

[pscustomobject]@{
    customerId = $customerId
    updated    = $true
}
