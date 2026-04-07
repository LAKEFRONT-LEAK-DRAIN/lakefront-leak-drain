# lakefront-leak-drain

## Daily 6:15 AM ET workflow email notice

A new workflow at `.github/workflows/daily_workflow_email.yml` sends a daily email by 6:15 AM America/New_York with status for all workflows in this repository.

It reports whether each one:

- ran successfully,
- is still in progress,
- was triggered but skipped,
- failed, or
- did not run today.

### Required repository secrets

Add these in GitHub: Settings -> Secrets and variables -> Actions -> New repository secret.

- `SMTP_SERVER` (example: `smtp.gmail.com`)
- `SMTP_PORT` (example: `465`)
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `ALERT_EMAIL_TO` (your recipient email)
- `ALERT_EMAIL_FROM` (the sender email address)

### Test it now

1. Go to Actions -> `Daily Workflow Email Notice`.
2. Click `Run workflow`.
3. Confirm you receive an email with today's status details and run links.

## Video text-to-visual alignment test workflow

Use `.github/workflows/video_gemini_alignment_test.yml` to test a stricter mode where Gemini:

- generates post copy first,
- generates targeted stock-video search queries from that copy,
- ranks candidate clips by relevance to the written post,
- then selects the best-matching candidate.

This test workflow is fully separate from production workflows. It runs `video_update_feed_alignment_test.py`, writes to `video_feed_alignment_test.xml`, and uploads artifacts for review.

## Live Video architecture

The repository now has a fully separate Live Video pipeline for Metricool and independent publishing.

- Feed file: `Live_Video_Feed.xml`
- Landing page path: `live-video/`
- Updater script: `live_video_update_feed.py`
- Workflow: `.github/workflows/live_video_gemini.yml`

This pipeline does not write to the original `video_feed.xml` or `video/` paths.

# Trigger: organization repo transfer test 2026-04-05

## Pending-tasks local auto-sync

This repo includes a local watcher that monitors only hcp-automation/pending-tasks and auto-commits plus pushes whenever JSON files change.

Scripts:

- hcp-automation/scripts/watch_pending_tasks_sync.ps1
- hcp-automation/scripts/register_pending_tasks_sync_task.ps1

Enable at Windows logon:

1. Open PowerShell in the repo root.
2. Run:

	powershell
	pwsh ./hcp-automation/scripts/register_pending_tasks_sync_task.ps1

What it does:

- Watches hcp-automation/pending-tasks/*.json.
- Stages only that folder.
- Creates an auto commit with timestamp.
- Pulls with rebase, then pushes to origin/main.

Notes:

- If push fails due to auth/network/conflict, the watcher keeps running and retries on the next file change.
- To stop using it, remove the scheduled task named LakefrontPendingTasksAutoSync from Task Scheduler.

## Pending-tasks cloud sync (Google Drive -> GitHub)

If you want sync to run even when your local computer is off, use Google Apps Script.

- Setup guide: hcp-automation/google-drive-sync/README.md
- Script file: hcp-automation/google-drive-sync/apps_script_sync.gs

This writes Drive JSON updates directly into hcp-automation/pending-tasks on GitHub, which triggers the existing HCP dispatcher workflow automatically.