# Google Drive to GitHub Pending-Tasks Sync

Use this to keep hcp-automation/pending-tasks in GitHub synced from a Google Drive folder without needing your local machine online.

## Files

- apps_script_sync.gs: Google Apps Script code

## Setup

1. In Google Drive, open the source folder that contains task JSON files.
2. Copy the folder ID from the URL.
3. Go to https://script.google.com and create a new script project.
4. Paste the code from apps_script_sync.gs into the editor.
5. Open Project Settings -> Script properties and set:
   - GITHUB_TOKEN
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

- Syncs only .json files from your Drive folder.
- Validates JSON before upload.
- Writes files into hcp-automation/pending-tasks on main.
- Tracks Drive file modified times to avoid duplicate commits.
- Each upload creates a GitHub commit, which triggers the existing workflow.

## Notes

- Keep JSON filenames unique in your Drive folder.
- If a JSON file in Drive is renamed, a new filename is created in GitHub.
- Deleted Drive files are not auto-deleted in GitHub by this version.
