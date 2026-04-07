param(
    [Parameter(Mandatory = $true)]
    [string]$customerId,

    [Parameter(Mandatory = $true)]
    [string]$street,

    [Parameter(Mandatory = $true)]
    [string]$city,

    [string]$state = "OH",
    [string]$zip = "44101",
    [string]$country = "US",
    [string]$type = "service"
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
    street  = $street
    city    = $city
    state   = $state
    zip     = $zip
    country = $country
    type    = $type
} | ConvertTo-Json

$url = "https://api.housecallpro.com/customers/$($customerId)/addresses"
$response = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $body

[pscustomobject]@{
    addressId = $response.id
}