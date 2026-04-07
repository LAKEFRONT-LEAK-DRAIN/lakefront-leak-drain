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

$name = "$($data.first_name) $($data.last_name)"
Write-Host "--- STARTING AUTOMATION FOR: $name ---"

$searchResult = & "$PSScriptRoot/hcp_search_customer.ps1" -searchTerm $name

if ($searchResult.matchFound -and -not [string]::IsNullOrWhiteSpace($searchResult.customerId)) {
    $customerId = $searchResult.customerId
    Write-Host "Using Existing Customer: $customerId"
}
else {
    $createResult = & "$PSScriptRoot/hcp_create_customer.ps1" -firstName $data.first_name -lastName $data.last_name
    $customerId = $createResult.customerId

    if ([string]::IsNullOrWhiteSpace($customerId)) {
        throw "Customer creation returned no customerId."
    }

    Write-Host "Created New Customer: $customerId"
}

$addrResult = & "$PSScriptRoot/hcp_add_address.ps1" -customerId $customerId -street $data.street -city $data.city
$addressId = $addrResult.addressId

if ([string]::IsNullOrWhiteSpace($addressId)) {
    throw "Address creation returned no addressId."
}

$priceCentsRaw = "$($data.price_cents)"
$priceCents = 0L

if (-not [long]::TryParse($priceCentsRaw, [ref]$priceCents)) {
    throw "Invalid price_cents value '$priceCentsRaw'. Provide a whole-number integer in cents."
}

if ($priceCents -le 0) {
    throw "Invalid price_cents value '$priceCentsRaw'. Value must be greater than 0."
}

$jobResult = & "$PSScriptRoot/hcp_create_work.ps1" -customerId $customerId -addressId $addressId -jobTitle $data.job_title -priceCents $priceCents

if ([string]::IsNullOrWhiteSpace($jobResult.jobId)) {
    throw "Job creation returned no jobId."
}

Write-Host "Job Created: $($jobResult.jobId)"
Write-Host "--- AUTOMATION COMPLETE ---"