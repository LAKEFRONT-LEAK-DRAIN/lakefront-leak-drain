# 1. AUTHENTICATION
$apiKey = $env:HCP_API_TOKEN
$headers = @{
    "Authorization" = "Token $($apiKey)"
    "Content-Type"  = "application/json"
    "Accept"        = "application/json"
}

# 2. DATA INPUT (This will be fed by the 'Pending-Tasks' folder later)
# For now, we use placeholders to test the logic
$firstName = "TEST_FIRST"
$lastName  = "TEST_LAST"
$mobile    = "555-555-5555"
$email     = "test@example.com"
$note      = "Created via Lakefront Automation Engine."

# 3. CONSTRUCT THE BODY
$body = @{
    first_name = $firstName
    last_name  = $lastName
    mobile_number = $mobile
    email = $email
    notes = $note
} | ConvertTo-Json

# 4. EXECUTE POST
$url = "https://api.housecallpro.com/customers"
$response = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $body

# 5. OUTPUT THE NEW ID (Crucial for the next steps)
Write-Host "SUCCESS: Customer Created."
Write-Host "NEW_CUSTOMER_ID: $($response.id)"