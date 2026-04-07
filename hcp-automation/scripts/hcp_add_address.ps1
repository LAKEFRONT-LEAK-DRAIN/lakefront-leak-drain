# 1. AUTHENTICATION
$apiKey = $env:HCP_API_TOKEN
$headers = @{
    "Authorization" = "Token $($apiKey)"
    "Content-Type"  = "application/json"
    "Accept"        = "application/json"
}

# 2. DYNAMIC INPUTS (To be fed by the 'Pending-Tasks' JSON)
$customerId = "INSERT_CUSTOMER_ID_HERE"
$street     = "123 MAIN ST"
$city       = "CLEVELAND"
$state      = "OH"
$zip        = "44101"

# 3. CONSTRUCT THE BODY
$body = @{
    street  = $street
    city    = $city
    state   = $state
    zip     = $zip
    country = "US"
    type    = "service"
} | ConvertTo-Json

# 4. EXECUTE POST (Using the Bulletproof URL Variable)
$url = "https://api.housecallpro.com/customers/$($customerId)/addresses"
$response = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $body

# 5. OUTPUT THE NEW ADDRESS ID
Write-Host "SUCCESS: Address Linked to Customer."
Write-Host "ADDRESS_ID: $($response.id)"