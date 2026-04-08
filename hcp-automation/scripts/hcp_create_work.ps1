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

function Parse-RequestedStartTime {
    param(
        [Parameter()]
        [AllowEmptyString()]
        [string]$RequestedSchedule
    )

    if ([string]::IsNullOrWhiteSpace($RequestedSchedule)) {
        return $null
    }

    $start = [datetime]::MinValue
    if (-not [datetime]::TryParse($RequestedSchedule, [ref]$start)) {
        return $null
    }

    return $start
}

function Get-HttpErrorBody {
    param(
        [Parameter(Mandatory = $true)]
        [System.Exception]$Exception
    )

    try {
        $resp = $Exception.Response
        if ($null -eq $resp) {
            return ""
        }
        $stream = $resp.GetResponseStream()
        if ($null -eq $stream) {
            return ""
        }
        $reader = New-Object System.IO.StreamReader($stream)
        return $reader.ReadToEnd()
    }
    catch {
        return ""
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

$requestedStart = Parse-RequestedStartTime -RequestedSchedule $requestedSchedule
if ($null -ne $requestedStart) {
    Write-Host "Schedule assignment: source=requested requested='$requestedSchedule' scheduled_start='$($requestedStart.ToString("yyyy-MM-ddTHH:mm:ss"))'"
}
else {
    Write-Host "Schedule assignment: source=default-anytime requested='$requestedSchedule'"
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

if ($null -ne $requestedStart -and -not [string]::IsNullOrWhiteSpace("$($response.id)")) {
    $requestedEnd = $requestedStart.AddHours(2)
    $appointmentUrl = "https://api.housecallpro.com/jobs/$($response.id)/appointments"

    $appointmentBodies = @(
        @{
            start_time = $requestedStart.ToString("o")
            end_time = $requestedEnd.ToString("o")
            arrival_window_minutes = 0
            dispatched_employees_ids = @($assignedTechId)
        },
        @{
            start_time = $requestedStart.ToString("yyyy-MM-ddTHH:mm:ss")
            end_time = $requestedEnd.ToString("yyyy-MM-ddTHH:mm:ss")
            arrival_window_minutes = 0
            dispatched_employees_ids = @($assignedTechId)
        },
        @{
            start_time = $requestedStart.ToString("o")
            end_time = $requestedEnd.ToString("o")
            arrival_window_minutes = 0
            dispatched_employee_ids = @($assignedTechId)
        }
    )

    $appointmentCreated = $false
    for ($i = 0; $i -lt $appointmentBodies.Count; $i++) {
        $attempt = $i + 1
        $appointmentBodyJson = $appointmentBodies[$i] | ConvertTo-Json -Depth 6
        try {
            $appointmentResponse = Invoke-RestMethod -Uri $appointmentUrl -Method Post -Headers $headers -Body $appointmentBodyJson
            Write-Host "Schedule assignment: appointment created id='$($appointmentResponse.id)' for job_id='$($response.id)' attempt=$attempt"
            $appointmentCreated = $true
            break
        }
        catch {
            $httpErrorBody = Get-HttpErrorBody -Exception $_.Exception
            Write-Host "Schedule assignment: appointment attempt=$attempt failed for job_id='$($response.id)' error='$($_.Exception.Message)' body='$httpErrorBody'"
        }
    }

    if (-not $appointmentCreated) {
        Write-Host "Schedule assignment: appointment creation failed for job_id='$($response.id)'; job remains anytime"
    }
}

[pscustomobject]@{
    jobId = $response.id
}