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

function Build-SchedulePayload {
    param(
        [Parameter()]
        [AllowEmptyString()]
        [string]$RequestedSchedule
    )

    if ([string]::IsNullOrWhiteSpace($RequestedSchedule)) {
        return @{
            anytime = $true
            anytime_start_date = (Get-Date).ToString("yyyy-MM-dd")
        }
    }

    $start = [datetime]::MinValue
    if (-not [datetime]::TryParse($RequestedSchedule, [ref]$start)) {
        return @{
            anytime = $true
            anytime_start_date = (Get-Date).ToString("yyyy-MM-dd")
        }
    }

    $end = $start.AddHours(2)
    return @{
        anytime = $false
        anytime_start_date = $start.ToString("yyyy-MM-dd")
        scheduled_start = $start.ToString("yyyy-MM-ddTHH:mm:ssK")
        scheduled_end = $end.ToString("yyyy-MM-ddTHH:mm:ssK")
        arrival_window_start = $start.ToString("yyyy-MM-ddTHH:mm:ssK")
        arrival_window_end = $end.ToString("yyyy-MM-ddTHH:mm:ssK")
    }
}

$costCents = [long][math]::Round(([decimal]$priceCents) * 0.50, 0)

$assignedTechId = $houseTech
$assignmentSource = "default"
if (-not [string]::IsNullOrWhiteSpace($requestedTechnician)) {
    $resolvedId = Resolve-RequestedTechnicianId -RequestedTechnician $requestedTechnician -Headers $headers
    if (-not [string]::IsNullOrWhiteSpace($resolvedId)) {
        $assignedTechId = $resolvedId
        $assignmentSource = "requested"
    }
}
Write-Host "Technician assignment: source=$assignmentSource requested='$requestedTechnician' assigned_id='$assignedTechId'"

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

$schedulePayload = Build-SchedulePayload -RequestedSchedule $requestedSchedule
$timedAttempt = ($schedulePayload.anytime -eq $false)
if ($timedAttempt) {
    Write-Host "Schedule assignment: source=requested requested='$requestedSchedule' scheduled_start='$($schedulePayload.scheduled_start)'"
}
else {
    Write-Host "Schedule assignment: source=default-anytime requested='$requestedSchedule'"
}

$body = @{
    customer_id = $customerId
    address_id  = $addressId
    assigned_employee_ids = @($assignedTechId)
    notes = $shieldNote
    schedule = $schedulePayload
    line_items = @(
        @{
            name       = $jobTitle
            unit_price = $priceCents
            unit_cost  = $costCents
            quantity   = 1
        }
    )
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "https://api.housecallpro.com/jobs" -Method Post -Headers $headers -Body $body
}
catch {
    if ($timedAttempt) {
        Write-Host "Schedule assignment: timed payload rejected by HCP, falling back to anytime"
        $fallbackBody = @{
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
        $response = Invoke-RestMethod -Uri "https://api.housecallpro.com/jobs" -Method Post -Headers $headers -Body $fallbackBody
    }
    else {
        throw
    }
}

[pscustomobject]@{
    jobId = $response.id
}