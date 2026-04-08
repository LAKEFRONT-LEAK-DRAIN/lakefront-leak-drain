param(
    [Parameter(Mandatory = $true)]
    [string]$customerId,

    [Parameter(Mandatory = $true)]
    [string]$addressId,

    [Parameter(Mandatory = $true)]
    [string]$jobTitle,

    [Parameter(Mandatory = $true)]
    [long]$priceCents,

    [string]$serviceSummary,
    [string]$requestedSchedule,
    [string]$requestedTechnician,
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

function Resolve-RequestedTechnicianId {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RequestedTechnician,

        [Parameter(Mandatory = $true)]
        [hashtable]$Headers
    )

    $needle = $RequestedTechnician.Trim()
    if ([string]::IsNullOrWhiteSpace($needle)) {
        return $null
    }

    if ($needle -like "pro_*") {
        return $needle
    }

    $needleLower = $needle.ToLowerInvariant()
    $page = 1
    $pageSize = 100

    while ($true) {
        $url = "https://api.housecallpro.com/employees?page=$page&page_size=$pageSize"
        $resp = Invoke-RestMethod -Uri $url -Method Get -Headers $Headers

        $employees = @($resp.employees)
        if ($employees.Count -eq 0) {
            break
        }

        foreach ($employee in $employees) {
            $fullName = ("$($employee.first_name) $($employee.last_name)").Trim()
            if ($fullName.ToLowerInvariant() -eq $needleLower) {
                return "$($employee.id)"
            }
        }

        foreach ($employee in $employees) {
            $fullName = ("$($employee.first_name) $($employee.last_name)").Trim().ToLowerInvariant()
            $email = ("$($employee.email)").Trim().ToLowerInvariant()
            $mobile = ("$($employee.mobile_number)").Trim().ToLowerInvariant()
            if (
                $fullName.Contains($needleLower) -or
                $needleLower.Contains($fullName) -or
                $email -eq $needleLower -or
                $mobile -eq $needleLower
            ) {
                return "$($employee.id)"
            }
        }

        $totalPages = [int]$resp.total_pages
        if ($page -ge $totalPages) {
            break
        }

        $page += 1
    }

    return $null
}

$costCents = [long][math]::Round(([decimal]$priceCents) * 0.50, 0)

$assignedTechId = $houseTech
if (-not [string]::IsNullOrWhiteSpace($requestedTechnician)) {
    $resolvedId = Resolve-RequestedTechnicianId -RequestedTechnician $requestedTechnician -Headers $headers
    if (-not [string]::IsNullOrWhiteSpace($resolvedId)) {
        $assignedTechId = $resolvedId
    }
}

$shieldNote = "--- SUMMARY OF WORK (COPY/PASTE) ---`n" +
              "I. SCOPE: $($jobTitle)`n" +
              "II. THE SHIELD: Successor Audit Required. Brittle Pipe Advisory.`n" +
              "III. MARGIN: 50% Cost Logic Applied."

if (-not [string]::IsNullOrWhiteSpace($serviceSummary)) {
    $shieldNote += "`nIV. SERVICE SUMMARY: $serviceSummary"
}

if (-not [string]::IsNullOrWhiteSpace($requestedSchedule)) {
    $shieldNote += "`nV. REQUESTED SCHEDULE: $requestedSchedule"
}

if (-not [string]::IsNullOrWhiteSpace($requestedTechnician)) {
    $shieldNote += "`nVI. REQUESTED TECHNICIAN: $requestedTechnician"
}

$body = @{
    customer_id = $customerId
    address_id  = $addressId
    assigned_employee_ids = @($assignedTechId)
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