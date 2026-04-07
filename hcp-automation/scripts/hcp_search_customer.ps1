param(
    [Parameter(Mandatory = $true)]
    [string]$searchTerm
)

$ErrorActionPreference = "Stop"

$apiKey = $env:HCP_API_TOKEN
if ([string]::IsNullOrWhiteSpace($apiKey)) {
    throw "HCP_API_TOKEN is missing."
}

$headers = @{
    "Authorization" = "Token $($apiKey)"
    "Accept"        = "application/json"
}

$url = "https://api.housecallpro.com/customers?q=$([Uri]::EscapeDataString($searchTerm))"
$response = Invoke-RestMethod -Uri $url -Method Get -Headers $headers

if ($response.customers.Count -gt 0) {
    $foundCustomer = $response.customers[0]
    [pscustomobject]@{
        matchFound       = $true
        customerId       = $foundCustomer.id
        primaryAddressId = if ($foundCustomer.addresses.Count -gt 0) { $foundCustomer.addresses[0].id } else { $null }
        fullName         = "$($foundCustomer.first_name) $($foundCustomer.last_name)"
    }
}
else {
    [pscustomobject]@{
        matchFound       = $false
        customerId       = $null
        primaryAddressId = $null
        fullName         = $null
    }
}