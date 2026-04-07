# 1. AUTHENTICATION & DEFAULTS
$apiKey = $env:HCP_API_TOKEN
$houseTech = "pro_0ea01a751b804d1e89a9cdaa7c1bbbc7" # Lakefront Technician

$headers = @{
    "Authorization" = "Token $($apiKey)"
    "Content-Type"  = "application/json"
    "Accept"        = "application/json"
}

# 2. DYNAMIC INPUTS (To be fed by the 'Pending-Tasks' JSON)
$customerId = "INSERT_CUSTOMER_ID_HERE"
$addressId  = "INSERT_ADDRESS_ID_HERE"
$jobTitle   = "Restoration: Main Line & Repipe"
$priceCents = 1000000 # $10,000.00
$costCents  = $priceCents * 0.50 # THE 50% LOGIC

# 3. THE SHIELD SUMMARY (Staging Area for Copy/Paste)
$shieldNote = "--- SUMMARY OF WORK (COPY/PASTE) ---`n" +
              "I. SCOPE: $($jobTitle)`n" +
              "II. THE SHIELD: Successor Audit Required. Brittle Pipe Advisory.`n" +
              "III. MARGIN: 50% Cost Logic Applied."

# 4. CONSTRUCT THE JOB BODY
$body = @{
    customer_id = $customerId
    address_id  = $addressId
    assigned_employee_ids = @($houseTech)
    notes = $shieldNote
    schedule = @{
        anytime = $true
        anytime_start_date = (Get-Date).ToString("yyyy-MM-dd")
    }
    line_items = @(
        @{
            name = $jobTitle
            unit_price = $priceCents
            unit_cost  = $costCents
            quantity = 1
        }
    )
} | ConvertTo-Json -Depth 10

# 5. EXECUTE POST
$url = "https://api.housecallpro.com/jobs"
$response = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $body

Write-Host "SUCCESS: Job Created and Assigned to House Tech."
Write-Host "JOB_ID: $($response.id)"