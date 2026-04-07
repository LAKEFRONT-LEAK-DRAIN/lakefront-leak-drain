param(
    [Parameter(Mandatory = $true)]
    [string]$firstName,

    [Parameter(Mandatory = $true)]
    [string]$lastName,

    [string]$mobile,
    [string]$email,
    [string]$note = "Created via Lakefront Automation Engine."
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
    notes      = $note
}

if (-not [string]::IsNullOrWhiteSpace($mobile)) {
    $body.mobile_number = $mobile
}

if (-not [string]::IsNullOrWhiteSpace($email)) {
    $body.email = $email
}

$response = Invoke-RestMethod -Uri "https://api.housecallpro.com/customers" -Method Post -Headers $headers -Body ($body | ConvertTo-Json)

[pscustomobject]@{
    customerId = $response.id
}