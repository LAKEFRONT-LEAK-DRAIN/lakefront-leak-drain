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