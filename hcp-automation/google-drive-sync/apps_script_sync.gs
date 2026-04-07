/**
 * Google Drive -> GitHub sync for pending task JSON files.
 *
 * Store settings in Script Properties:
 * - GITHUB_TOKEN: Fine-grained PAT with Contents Read/Write on this repo
 * - GITHUB_OWNER: lakefrontleakanddrain-design
 * - GITHUB_REPO: lakefront-leak-drain
 * - GITHUB_BRANCH: main
 * - DRIVE_FOLDER_ID: source folder containing task JSON files
 */

function syncPendingTasksToGitHub() {
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(30000)) {
    Logger.log("Another sync is already running. Skipping this run.");
    return;
  }

  try {
    var cfg = getConfig_();
    var state = getState_();
    var nextState = {};

    var folder = DriveApp.getFolderById(cfg.driveFolderId);
    var files = folder.getFilesByType(MimeType.PLAIN_TEXT);
    var pushedCount = 0;

    while (files.hasNext()) {
      var file = files.next();
      var name = file.getName();

      if (!/\.json$/i.test(name)) {
        continue;
      }

      var fileId = file.getId();
      var modifiedAt = file.getLastUpdated().toISOString();
      nextState[fileId] = modifiedAt;

      if (state[fileId] && state[fileId] === modifiedAt) {
        continue;
      }

      var content = file.getBlob().getDataAsString("UTF-8");
      validateJson_(content, name);

      var targetPath = "hcp-automation/pending-tasks/" + sanitizeFileName_(name);
      upsertGitHubFile_(cfg, targetPath, content, "sync pending-task from drive: " + name);
      pushedCount++;
    }

    setState_(nextState);
    Logger.log("Sync complete. Pushed " + pushedCount + " changed file(s).");
  } finally {
    lock.releaseLock();
  }
}

function getConfig_() {
  var props = PropertiesService.getScriptProperties();

  var cfg = {
    githubToken: props.getProperty("GITHUB_TOKEN"),
    owner: props.getProperty("GITHUB_OWNER"),
    repo: props.getProperty("GITHUB_REPO"),
    branch: props.getProperty("GITHUB_BRANCH") || "main",
    driveFolderId: props.getProperty("DRIVE_FOLDER_ID")
  };

  var missing = [];
  if (!cfg.githubToken) missing.push("GITHUB_TOKEN");
  if (!cfg.owner) missing.push("GITHUB_OWNER");
  if (!cfg.repo) missing.push("GITHUB_REPO");
  if (!cfg.driveFolderId) missing.push("DRIVE_FOLDER_ID");

  if (missing.length > 0) {
    throw new Error("Missing Script Properties: " + missing.join(", "));
  }

  return cfg;
}

function getState_() {
  var raw = PropertiesService.getScriptProperties().getProperty("SYNC_STATE_JSON");
  if (!raw) {
    return {};
  }

  try {
    return JSON.parse(raw);
  } catch (err) {
    Logger.log("Invalid state found; resetting. " + err);
    return {};
  }
}

function setState_(stateObj) {
  PropertiesService.getScriptProperties().setProperty("SYNC_STATE_JSON", JSON.stringify(stateObj));
}

function validateJson_(content, fileName) {
  try {
    JSON.parse(content);
  } catch (err) {
    throw new Error("Invalid JSON in file " + fileName + ": " + err);
  }
}

function sanitizeFileName_(name) {
  return name.replace(/[^a-zA-Z0-9._-]/g, "_");
}

function upsertGitHubFile_(cfg, path, content, commitMessage) {
  var existing = getGitHubFileSha_(cfg, path);
  var url = "https://api.github.com/repos/" + cfg.owner + "/" + cfg.repo + "/contents/" + encodePath_(path);
  var payload = {
    message: commitMessage,
    content: Utilities.base64Encode(content, Utilities.Charset.UTF_8),
    branch: cfg.branch
  };

  if (existing.sha) {
    payload.sha = existing.sha;
  }

  var response = UrlFetchApp.fetch(url, {
    method: "put",
    contentType: "application/json",
    headers: {
      Authorization: "Bearer " + cfg.githubToken,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28"
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });

  var code = response.getResponseCode();
  if (code < 200 || code > 299) {
    throw new Error("GitHub upsert failed for " + path + " with HTTP " + code + ": " + response.getContentText());
  }
}

function getGitHubFileSha_(cfg, path) {
  var url = "https://api.github.com/repos/" + cfg.owner + "/" + cfg.repo + "/contents/" + encodePath_(path) + "?ref=" + encodeURIComponent(cfg.branch);
  var response = UrlFetchApp.fetch(url, {
    method: "get",
    headers: {
      Authorization: "Bearer " + cfg.githubToken,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28"
    },
    muteHttpExceptions: true
  });

  var code = response.getResponseCode();
  if (code === 404) {
    return { sha: null };
  }

  if (code < 200 || code > 299) {
    throw new Error("GitHub SHA lookup failed for " + path + " with HTTP " + code + ": " + response.getContentText());
  }

  var body = JSON.parse(response.getContentText());
  return { sha: body.sha || null };
}

function encodePath_(path) {
  return path.split("/").map(encodeURIComponent).join("/");
}
