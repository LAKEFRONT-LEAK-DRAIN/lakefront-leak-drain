param(
    [Parameter(Mandatory = $true)]
    [string]$customerId,

    [Parameter(Mandatory = $true)]
    [string]$addressId,

    [Parameter(Mandatory = $true)]
    [string]$jobTitle,

    [Parameter(Mandatory = $true)]
    [int]$priceCents,

    [string]$houseTech = "pro_0ea01a751b804d1e89a9cdaa7c1bbbc7"
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

$costCents = [int][math]::Round($priceCents * 0.50)

$shieldNote = "--- SUMMARY OF WORK (COPY/PASTE) ---`n" +
              "I. SCOPE: $($jobTitle)`n" +
              "II. THE SHIELD: Successor Audit Required. Brittle Pipe Advisory.`n" +
              "III. MARGIN: 50% Cost Logic Applied."

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
            name       = $jobTitle
            unit_price = $priceCents
            unit_cost  = $costCents
            quantity   = 1
        }
    )
} | ConvertTo-Json -Depth 10

$response = Invoke-RestMethod -Uri "https://api.housecallpro.com/jobs" -Method Post -Headers $headers -Body $body

[pscustomobject]@{
    jobId = $response.id
}