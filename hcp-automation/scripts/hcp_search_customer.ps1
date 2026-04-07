# Set up the API connection using your Secret Key
$apiKey = $env:HCP_API_TOKEN
$headers = @{
    "Authorization" = "Token $($apiKey)"
    "Accept"        = "application/json"
}

# The Search Term (We will pass this dynamically later)
$searchTerm = "Gemini Jones" 

# EXECUTE SEARCH
$url = "https://api.housecallpro.com/customers?q=$([Uri]::EscapeDataString($searchTerm))"
$response = Invoke-RestMethod -Uri $url -Method Get -Headers $headers

if ($response.customers.Count -gt 0) {
    $foundCustomer = $response.customers[0]
    Write-Host "MATCH FOUND: $($foundCustomer.first_name) $($foundCustomer.last_name)"
    Write-Host "CUSTOMER_ID: $($foundCustomer.id)"
    
    # Grab the primary address ID
    if ($foundCustomer.addresses.Count -gt 0) {
        Write-Host "PRIMARY_ADDRESS_ID: $($foundCustomer.addresses[0].id)"
    }
} else {
    Write-Host "NO MATCH FOUND. Proceed to Step 2: Create Customer."
}