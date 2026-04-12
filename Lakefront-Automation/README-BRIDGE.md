# Pending Tasks Bridge (Gemini -> GitHub)

This service accepts a JSON payload and writes only to:

- hcp-automation/pending-tasks/*.json

It is designed to let Gemini create customer tasks hands-free while keeping your GitHub token on the server side.

## Files

- pending_tasks_bridge.py
- requirements-bridge.txt
- Dockerfile
- bridge.env.example

## 1) Create required secrets

- BRIDGE_API_KEY: long random secret (used in x-bridge-key header)
- GITHUB_TOKEN: fine-grained PAT with Contents read/write for this repo only

## 2) Deploy to Cloud Run

From this folder (Lakefront-Automation):

```powershell
$PROJECT_ID = "your-gcp-project-id"
$REGION = "us-central1"
$SERVICE = "lakefront-pending-tasks-bridge"
$BRIDGE_KEY = "replace-with-long-random-secret"
$GITHUB_TOKEN = "replace-with-fine-grained-github-pat"

gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --project $PROJECT_ID

gcloud run deploy $SERVICE `
  --source . `
  --project $PROJECT_ID `
  --region $REGION `
  --allow-unauthenticated `
  --set-env-vars "BRIDGE_API_KEY=$BRIDGE_KEY,GITHUB_TOKEN=$GITHUB_TOKEN,GITHUB_OWNER=lakefrontleakanddrain-design,GITHUB_REPO=lakefront-leak-drain,GITHUB_BRANCH=main,GITHUB_PENDING_TASKS_PATH=hcp-automation/pending-tasks"

$URL = gcloud run services describe $SERVICE --region $REGION --project $PROJECT_ID --format "value(status.url)"
$URL
```

## 3) Test endpoint

```powershell
Invoke-RestMethod -Uri "$URL/healthz" -Method Get
```

```powershell
$body = @{
  first_name = "Megan"
  last_name = "Featherston"
  street = "8707 GROVESIDE DR"
  city = "STRONGSVILLE"
  state = "OH"
  zip = "44118"
  phone = "216-505-7765"
  email = "who.b00yah@gmail.com"
  job_title = "Estimate: basement pipe replacement, exterior water line replacement, reroute water heater feed"
  price_cents = 100
  requested_technician = "Richard Cooper"
  requested_schedule = "Tomorrow 9:00 AM"
  service_summary = "Estimate to replace basement plumbing pipes, replace exterior water lines, and reroute water heater feed."
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "$URL/create-pending-task" `
  -Method Post `
  -Headers @{ "x-bridge-key" = $BRIDGE_KEY } `
  -ContentType "application/json" `
  -Body $body
```

## 4) Gemini call contract

- Method: POST
- URL: https://<your-cloud-run-url>/create-pending-task
- Header: x-bridge-key: <your BRIDGE_API_KEY>
- Body keys:
  - Required: first_name, last_name, street, city, job_title
  - Recommended: state, zip, phone, email, requested_technician, requested_schedule, service_summary, price_cents
  - Optional: line_items (array of { name, unit_price, quantity })

## 5) Email intake endpoint (Gemini-assisted extraction)

If Gemini already has email access, you can send raw email text to the bridge and let the server-side Gemini extraction normalize it.

- Method: POST
- URL: https://<your-cloud-run-url>/intake
- Header: x-bridge-key: <your BRIDGE_API_KEY>
- Body keys:
  - text or email_body (required)
  - email_subject (optional)
  - email_from (optional)
  - email_received_at (optional)

Example:

```powershell
$body = @{
  email_from = "dispatch@warranty-company.example"
  email_subject = "Accepted Work Order #12345"
  email_received_at = "2026-04-12T09:10:00-04:00"
  email_body = "<paste full accepted work-order email text here>"
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "$URL/intake" `
  -Method Post `
  -Headers @{ "x-bridge-key" = $BRIDGE_KEY } `
  -ContentType "application/json" `
  -Body $body
```

## 6) Security notes

- Never put GITHUB_TOKEN in Gemini prompts.
- Keep BRIDGE_API_KEY private.
- Rotate GITHUB_TOKEN and BRIDGE_API_KEY periodically.
