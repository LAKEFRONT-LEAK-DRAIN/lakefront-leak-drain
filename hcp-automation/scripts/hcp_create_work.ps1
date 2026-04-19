param(
    [Parameter(Mandatory = $true)]
    [string]$customerId,

    [Parameter(Mandatory = $true)]
    [string]$addressId,

    [Parameter(Mandatory = $true)]
    [string]$jobTitle,

    [Parameter(Mandatory = $true)]
    [long]$priceCents,

    [string]$lineItemsJson,
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

    $raw = $RequestedSchedule.Trim()
    $lower = $raw.ToLowerInvariant()
    $today = (Get-Date).Date

    # Handle common natural phrases first (today/tomorrow + time).
    if ($lower -match "^today(?:\s+at)?\s+(.+)$") {
        $timePart = $Matches[1].Trim()
        $raw = "{0} {1}" -f $today.ToString("yyyy-MM-dd"), $timePart
    }
    elseif ($lower -match "^tomorrow(?:\s+at)?\s+(.+)$") {
        $timePart = $Matches[1].Trim()
        $raw = "{0} {1}" -f $today.AddDays(1).ToString("yyyy-MM-dd"), $timePart
    }
    elseif ($lower -match "^\d{1,2}(?::\d{2})?\s*(am|pm)$") {
        # Time-only input means "today at" that time.
        $raw = "{0} {1}" -f $today.ToString("yyyy-MM-dd"), $raw
    }

    # Handle common range input by using the range start (e.g., "Monday 4/13/2026 11-3 pm" -> "Monday 4/13/2026 11 pm").
    if ($raw -match "^(?<datePart>.+?)\s+(?<startHour>\d{1,2})(?::(?<startMinute>\d{2}))?\s*-\s*(?<endHour>\d{1,2})(?::(?<endMinute>\d{2}))?\s*(?<ampm>am|pm)$") {
        $datePart = $Matches["datePart"].Trim()
        $startHour = $Matches["startHour"]
        $startMinute = $Matches["startMinute"]
        $ampm = $Matches["ampm"]

        $startToken = if ([string]::IsNullOrWhiteSpace($startMinute)) {
            "$startHour $ampm"
        }
        else {
            "$startHour`:$startMinute $ampm"
        }

        $raw = "$datePart $startToken"
    }

    $start = [datetime]::MinValue
    $styles = [System.Globalization.DateTimeStyles]::AssumeLocal
    $formats = @(
        "yyyy-MM-dd h:mmtt",
        "yyyy-MM-dd h:mm tt",
        "yyyy-MM-dd htt",
        "yyyy-MM-dd h tt",
        "yyyy-MM-dd H:mm",
        "M/d/yyyy h:mmtt",
        "M/d/yyyy h:mm tt",
        "M/d/yyyy H:mm"
    )

    if (
        -not [datetime]::TryParseExact($raw, $formats, [System.Globalization.CultureInfo]::InvariantCulture, $styles, [ref]$start) -and
        -not [datetime]::TryParse($raw, [System.Globalization.CultureInfo]::InvariantCulture, $styles, [ref]$start) -and
        -not [datetime]::TryParse($raw, [ref]$start)
    ) {
        return $null
    }

    return $start
}

function Parse-RequestedTimeWindow {
    param(
        [Parameter()]
        [AllowEmptyString()]
        [string]$RequestedSchedule
    )

    if ([string]::IsNullOrWhiteSpace($RequestedSchedule)) {
        return $null
    }

    $raw = $RequestedSchedule.Trim()

    # Remove common labels emitted by warranty emails.
    $raw = $raw -replace '(?i)Appointment\s*:\s*', ''
    $raw = $raw -replace '(?i)Time\s*Slot\s*:\s*', ' '

    # Normalize separators and collapse whitespace.
    $raw = $raw -replace '\s*[–—]\s*', '-'
    $raw = ($raw -replace '\s+', ' ').Trim()

    # Remove ordinal suffixes from day numbers (14th -> 14) for reliable parsing.
    $raw = [regex]::Replace($raw, '(?i)\b(\d{1,2})(st|nd|rd|th)\b', '$1')

    $windowRegexes = @(
        # Tuesday April 14, 2026 07:00 AM-11:00 AM
        '^(?<datePart>.+?),\s*(?<year>\d{4})\s+(?<start>\d{1,2}:\d{2}\s*(?:AM|PM))\s*-\s*(?<end>\d{1,2}:\d{2}\s*(?:AM|PM))$'
        # Tuesday April 14, 2026 7 AM-11 AM
        '^(?<datePart>.+?),\s*(?<year>\d{4})\s+(?<start>\d{1,2}\s*(?:AM|PM))\s*-\s*(?<end>\d{1,2}\s*(?:AM|PM))$'
        # Tuesday 4/14/2026 07:00 AM-11:00 AM
        '^(?<datePart>.+?)\s+(?<start>\d{1,2}:\d{2}\s*(?:AM|PM))\s*-\s*(?<end>\d{1,2}:\d{2}\s*(?:AM|PM))$'
        # Tuesday 4/14/2026 11-3 PM (single meridiem at end)
        '^(?<datePart>.+?)\s+(?<startHour>\d{1,2})(?::(?<startMinute>\d{2}))?\s*-\s*(?<endHour>\d{1,2})(?::(?<endMinute>\d{2}))?\s*(?<ampm>AM|PM)$'
    )

    foreach ($pattern in $windowRegexes) {
        $m = [regex]::Match($raw, $pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
        if (-not $m.Success) {
            continue
        }

        if ($m.Groups['datePart'].Success -and $m.Groups['year'].Success) {
            $datePart = ($m.Groups['datePart'].Value.Trim() + ', ' + $m.Groups['year'].Value.Trim()).Trim()
        }
        else {
            $datePart = $m.Groups['datePart'].Value.Trim()
        }

        $startToken = ''
        $endToken = ''

        if ($m.Groups['start'].Success -and $m.Groups['end'].Success) {
            $startToken = $m.Groups['start'].Value.Trim().ToUpperInvariant()
            $endToken = $m.Groups['end'].Value.Trim().ToUpperInvariant()
        }
        elseif ($m.Groups['startHour'].Success -and $m.Groups['endHour'].Success -and $m.Groups['ampm'].Success) {
            $ampm = $m.Groups['ampm'].Value.Trim().ToUpperInvariant()

            $startToken = if ($m.Groups['startMinute'].Success -and -not [string]::IsNullOrWhiteSpace($m.Groups['startMinute'].Value)) {
                "$($m.Groups['startHour'].Value):$($m.Groups['startMinute'].Value) $ampm"
            }
            else {
                "$($m.Groups['startHour'].Value) $ampm"
            }

            $endToken = if ($m.Groups['endMinute'].Success -and -not [string]::IsNullOrWhiteSpace($m.Groups['endMinute'].Value)) {
                "$($m.Groups['endHour'].Value):$($m.Groups['endMinute'].Value) $ampm"
            }
            else {
                "$($m.Groups['endHour'].Value) $ampm"
            }
        }

        $start = Parse-RequestedStartTime -RequestedSchedule "$datePart $startToken"
        $end = Parse-RequestedStartTime -RequestedSchedule "$datePart $endToken"

        if ($null -ne $start -and $null -ne $end) {
            if ($end -le $start) {
                $end = $end.AddDays(1)
            }

            return [pscustomobject]@{
                Start = $start
                End   = $end
            }
        }
    }

    $singleStart = Parse-RequestedStartTime -RequestedSchedule $raw
    if ($null -ne $singleStart) {
        return [pscustomobject]@{
            Start = $singleStart
            End   = $singleStart.AddHours(2)
        }
    }

    return $null
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

$defaultLineItem = @{
    name       = $jobTitle
    unit_price = $priceCents
    unit_cost  = $costCents
    quantity   = 1
}
if (-not [string]::IsNullOrWhiteSpace($serviceSummary)) {
    $defaultLineItem.description = $serviceSummary
}
$jobLineItems = @($defaultLineItem)

if (-not [string]::IsNullOrWhiteSpace($lineItemsJson)) {
    try {
        $parsedLineItems = ConvertFrom-Json -InputObject $lineItemsJson
        $candidateItems = @($parsedLineItems)

        if ($candidateItems.Count -gt 0) {
            $validated = @()

            foreach ($item in $candidateItems) {
                $name = "$($item.name)".Trim()
                if ([string]::IsNullOrWhiteSpace($name)) {
                    continue
                }

                $unitPrice = 0L
                if (-not [long]::TryParse("$($item.unit_price)", [ref]$unitPrice)) {
                    throw "line_items contains invalid unit_price: '$($item.unit_price)'"
                }

                if ($unitPrice -lt 0) {
                    throw "line_items contains negative unit_price: '$($item.unit_price)'"
                }

                $quantity = 1
                if (-not [int]::TryParse("$($item.quantity)", [ref]$quantity)) {
                    $quantity = 1
                }
                if ($quantity -lt 1) {
                    $quantity = 1
                }

                $unitCost = [long][math]::Round(([decimal]$unitPrice) * 0.50, 0)

                $lineItemDescription = "$($item.description)".Trim()
                if ([string]::IsNullOrWhiteSpace($lineItemDescription)) {
                    $lineItemDescription = $serviceSummary
                }

                $validatedItem = @{
                    name       = $name
                    unit_price = $unitPrice
                    unit_cost  = $unitCost
                    quantity   = $quantity
                }
                if (-not [string]::IsNullOrWhiteSpace($lineItemDescription)) {
                    $validatedItem.description = $lineItemDescription
                }
                $validated += $validatedItem
            }

            if ($validated.Count -gt 0) {
                $jobLineItems = $validated
            }
        }
    }
    catch {
        throw "Invalid lineItemsJson payload. $($_.Exception.Message)"
    }
}

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
              "I. SCOPE: $($jobTitle)"

if (-not [string]::IsNullOrWhiteSpace($serviceSummary)) {
    $shieldNote += "`nII. SERVICE SUMMARY: $serviceSummary"
}

if (-not [string]::IsNullOrWhiteSpace($requestedSchedule)) {
    $shieldNote += "`nIII. REQUESTED SCHEDULE: $requestedSchedule"
}

if (-not [string]::IsNullOrWhiteSpace($requestedTechnician)) {
    $shieldNote += "`nIV. REQUESTED TECHNICIAN: $requestedTechnician"
}

$requestedWindow = Parse-RequestedTimeWindow -RequestedSchedule $requestedSchedule
if ($null -ne $requestedWindow -and $null -ne $requestedWindow.Start) {
    Write-Host "Schedule assignment: source=requested requested='$requestedSchedule' scheduled_start='$($requestedWindow.Start.ToString("yyyy-MM-ddTHH:mm:ss"))' scheduled_end='$($requestedWindow.End.ToString("yyyy-MM-ddTHH:mm:ss"))'"
}
else {
    Write-Host "Schedule assignment: source=default-anytime requested='$requestedSchedule'"
}

$jobPayload = @{
    customer_id = $customerId
    address_id  = $addressId
    assigned_employee_ids = @($assignedTechId)
    notes = $shieldNote
    line_items = $jobLineItems
}

if ($null -eq $requestedWindow -or $null -eq $requestedWindow.Start) {
    $jobPayload.schedule = @{
        anytime = $true
        anytime_start_date = (Get-Date).ToString("yyyy-MM-dd")
    }
}

$body = $jobPayload | ConvertTo-Json -Depth 10

$response = Invoke-RestMethod -Uri "https://api.housecallpro.com/jobs" -Method Post -Headers $headers -Body $body

if ($null -ne $requestedWindow -and $null -ne $requestedWindow.Start -and -not [string]::IsNullOrWhiteSpace("$($response.id)")) {
    $requestedStart = $requestedWindow.Start
    $requestedEnd = $requestedWindow.End
    $appointmentUrl = "https://api.housecallpro.com/jobs/$($response.id)/appointments"

    $startOffset = [datetimeoffset]::new($requestedStart, [System.TimeZoneInfo]::Local.GetUtcOffset($requestedStart))
    $endOffset = [datetimeoffset]::new($requestedEnd, [System.TimeZoneInfo]::Local.GetUtcOffset($requestedEnd))

    $appointmentBodies = @(
        @{
            start_time = $startOffset.ToString("o")
            end_time = $endOffset.ToString("o")
            arrival_window_minutes = 0
            dispatched_employees_ids = @($assignedTechId)
        },
        @{
            start_time = $startOffset.ToString("yyyy-MM-ddTHH:mm:sszzz")
            end_time = $endOffset.ToString("yyyy-MM-ddTHH:mm:sszzz")
            arrival_window_minutes = 0
            dispatched_employees_ids = @($assignedTechId)
        },
        @{
            start_time = $startOffset.ToString("o")
            end_time = $endOffset.ToString("o")
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