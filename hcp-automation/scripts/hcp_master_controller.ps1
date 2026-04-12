[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$taskFile
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -Path $taskFile)) {
    throw "Task file not found: $taskFile"
}

$data = Get-Content -Path $taskFile -Raw | ConvertFrom-Json

$requiredFields = @("first_name", "last_name", "street", "city", "job_title", "price_cents")
foreach ($field in $requiredFields) {
    if (-not $data.PSObject.Properties.Name.Contains($field) -or [string]::IsNullOrWhiteSpace("$($data.$field)")) {
        throw "Task file is missing required field: $field"
    }
}

function Normalize-OptionalContactValue {
    param(
        [Parameter()]
        [AllowNull()]
        [string]$Value
    )

    $trimmed = "$Value".Trim()
    if ([string]::IsNullOrWhiteSpace($trimmed)) {
        return ""
    }

    if ($trimmed -match '^(?i:none|null|n/?a|na)$') {
        return ""
    }

    return $trimmed
}

$name = "$($data.first_name) $($data.last_name)"
Write-Host "--- STARTING AUTOMATION FOR: $name ---"

$searchResult = & "$PSScriptRoot/hcp_search_customer.ps1" -searchTerm $name

if ($searchResult.matchFound -and -not [string]::IsNullOrWhiteSpace($searchResult.customerId)) {
    $customerId = $searchResult.customerId
    Write-Host "Using Existing Customer: $customerId"
}
else {
    $companyName = Normalize-OptionalContactValue -Value "$($data.company_name)"
    $mobile = Normalize-OptionalContactValue -Value "$($data.phone)"
    $email = Normalize-OptionalContactValue -Value "$($data.email)"
    $displayName = ""
    if (-not [string]::IsNullOrWhiteSpace($companyName) -and $companyName.Trim().ToLowerInvariant() -eq "choice home warranty") {
        $displayName = "$($data.first_name) $($data.last_name) Choice Home Warranty".Trim()
    }

    $createResult = & "$PSScriptRoot/hcp_create_customer.ps1" -firstName $data.first_name -lastName $data.last_name -companyName $companyName -mobile $mobile -email $email -displayName $displayName
    $customerId = $createResult.customerId

    if ([string]::IsNullOrWhiteSpace($customerId)) {
        throw "Customer creation returned no customerId."
    }

    Write-Host "Created New Customer: $customerId"
}

$priceCentsRaw = "$($data.price_cents)"
$priceCents = 0L

if (-not [long]::TryParse($priceCentsRaw, [ref]$priceCents)) {
    throw "Invalid price_cents value '$priceCentsRaw'. Provide a whole-number integer in cents."
}

if ($priceCents -lt 0) {
    throw "Invalid price_cents value '$priceCentsRaw'. Value cannot be negative."
}

$state = Normalize-OptionalContactValue -Value "$($data.state)"
if ([string]::IsNullOrWhiteSpace($state)) {
    $state = "OH"
}

$zip = Normalize-OptionalContactValue -Value "$($data.zip)"
if ([string]::IsNullOrWhiteSpace($zip)) {
    $zip = "44101"
}

$addrResult = & "$PSScriptRoot/hcp_add_address.ps1" -customerId $customerId -street $data.street -city $data.city -state $state -zip $zip
$addressId = $addrResult.addressId

if ([string]::IsNullOrWhiteSpace($addressId)) {
    throw "Address creation returned no addressId."
}

$serviceSummary = Normalize-OptionalContactValue -Value "$($data.service_summary)"
$requestedSchedule = Normalize-OptionalContactValue -Value "$($data.requested_schedule)"
$requestedTechnician = Normalize-OptionalContactValue -Value "$($data.requested_technician)"

$lineItemsJson = ""
if ($data.PSObject.Properties.Name.Contains("line_items") -and $null -ne $data.line_items) {
    if ($data.line_items -is [System.Collections.IEnumerable] -and -not ($data.line_items -is [string])) {
        $lineItemsJson = ($data.line_items | ConvertTo-Json -Depth 10 -Compress)
    }
}

$jobResult = & "$PSScriptRoot/hcp_create_work.ps1" -customerId $customerId -addressId $addressId -jobTitle $data.job_title -priceCents $priceCents -serviceSummary $serviceSummary -requestedSchedule $requestedSchedule -requestedTechnician $requestedTechnician -lineItemsJson $lineItemsJson

if ([string]::IsNullOrWhiteSpace($jobResult.jobId)) {
    throw "Job creation returned no jobId."
}

Write-Host "Job Created: $($jobResult.jobId)"
Write-Host "--- AUTOMATION COMPLETE ---"