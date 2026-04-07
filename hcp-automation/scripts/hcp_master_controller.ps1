# MASTER CONTROLLER: Runs the Full Sequence
param($taskFile)

# 1. Load the Task Data
$data = Get-Content $taskFile | ConvertFrom-Json
$name = "$($data.first_name) $($data.last_name)"

Write-Host "--- STARTING AUTOMATION FOR: $name ---"

# 2. RUN SEARCH
$searchResult = . "$PSScriptRoot/hcp_search_customer.ps1" -searchTerm $name

if ($searchResult -like "*MATCH FOUND*") {
    $customerId = ($searchResult | Select-String "CUSTOMER_ID: (.*)").Matches.Groups[1].Value
    Write-Host "Using Existing Customer: $customerId"
} else {
    # 3. RUN CREATE CUSTOMER (If not found)
    $createResult = . "$PSScriptRoot/hcp_create_customer.ps1" -firstName $data.first_name -lastName $data.last_name
    $customerId = ($createResult | Select-String "NEW_CUSTOMER_ID: (.*)").Matches.Groups[1].Value
    Write-Host "Created New Customer: $customerId"
}

# 4. RUN ADDRESS LINKER
$addrResult = . "$PSScriptRoot/hcp_add_address.ps1" -customerId $customerId -street $data.street -city $data.city
$addressId = ($addrResult | Select-String "ADDRESS_ID: (.*)").Matches.Groups[1].Value

# 5. RUN REVENUE ENGINE (Create Job)
. "$PSScriptRoot/hcp_create_work.ps1" -customerId $customerId -addressId $addressId -jobTitle $data.job_title -priceCents $data.price_cents

Write-Host "--- AUTOMATION COMPLETE ---"