# Google Drive to GitHub Pending-Tasks Sync

Use this to keep hcp-automation/pending-tasks in GitHub synced from a Google Drive folder without needing your local machine online.

## Files

- apps_script_sync.gs: Google Apps Script code

## Setup

1. In Google Drive, open the source folder that contains either:
   - .json files, or
   - Google Docs where the doc body is raw JSON text.
2. Copy the folder ID from the URL.
3. Go to https://script.google.com and create a new script project.
4. Paste the code from apps_script_sync.gs into the editor.
5. Open Project Settings -> Script properties and set:
   - GITHUB_TOKEN = (paste your token here — do NOT save it in this file)
   - GITHUB_OWNER = lakefrontleakanddrain-design
   - GITHUB_REPO = lakefront-leak-drain
   - GITHUB_BRANCH = main
   - DRIVE_FOLDER_ID = 1GtobaFzFgmif5nXUsXUD0xJrWvPsl5X2
6. Create a fine-grained GitHub token with Contents read/write on this repo.
7. Run syncPendingTasksToGitHub once manually and approve permissions.
8. In Apps Script, add a Trigger:
   - Function: syncPendingTasksToGitHub
   - Event source: Time-driven
   - Interval: Every 5 minutes

## Behavior

- Syncs source tasks from your Drive folder using either .json files or Google Docs.
- Validates JSON before upload.
- Writes files into hcp-automation/pending-tasks on main.
- Tracks Drive file modified times to avoid duplicate commits.
- Each upload creates a GitHub commit, which triggers the existing workflow.

### Google Doc mapping

- If the source is a Google Doc, output filename is deterministic and unique:
   - doc-<google-file-id>.json
- This avoids collisions if multiple docs have the same title.

## Notes

- Keep JSON filenames unique in your Drive folder.
- If a JSON file in Drive is renamed, a new filename is created in GitHub.
- For Google Docs, renaming the doc does not change output filename because it is based on file ID.
- Deleted Drive files are not auto-deleted in GitHub by this version.
