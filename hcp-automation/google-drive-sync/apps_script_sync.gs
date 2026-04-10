/**
 * Google Drive -> GitHub sync for pending task JSON content.
 *
 * Store settings in Script Properties:
 * - GITHUB_TOKEN: Fine-grained PAT with Contents Read/Write on this repo
 * - GITHUB_OWNER: lakefrontleakanddrain-design
 * - GITHUB_REPO: lakefront-leak-drain
 * - GITHUB_BRANCH: main
 * - DRIVE_FOLDER_ID: source folder containing JSON files and/or Google Docs with JSON text
 * - DOC_FILENAME_MODE: title (default) or doc_id
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
    var files = folder.getFiles();
    var pushedCount = 0;

    while (files.hasNext()) {
      var file = files.next();
      var name = file.getName();
      var fileId = file.getId();
      var mimeType = file.getMimeType();

      if (!isSupportedSource_(name, mimeType)) {
        continue;
      }

      var modifiedAt = file.getLastUpdated().toISOString();
      nextState[fileId] = modifiedAt;

      if (state[fileId] && state[fileId] === modifiedAt) {
        continue;
      }

      var sourceText = readSourceText_(fileId, mimeType);
      var jsonText = normalizeJsonText_(sourceText, name);

      var targetFileName = buildTargetFileName_(name, fileId, mimeType, cfg);
      var targetPath = "hcp-automation/pending-tasks/" + targetFileName;
      upsertGitHubFile_(cfg, targetPath, jsonText, "sync pending-task from drive: " + name);

      pushedCount++;
    }

    setState_(nextState);
    Logger.log("Sync complete. Pushed " + pushedCount + " changed file(s).");
  } finally {
    lock.releaseLock();
  }
}

function getConfig_() {
  var props = getScriptPropertiesWithRetry_();

  var cfg = {
    githubToken: props.getProperty("GITHUB_TOKEN"),
    owner: props.getProperty("GITHUB_OWNER"),
    repo: props.getProperty("GITHUB_REPO"),
    branch: props.getProperty("GITHUB_BRANCH") || "main",
    driveFolderId: props.getProperty("DRIVE_FOLDER_ID"),
    docFilenameMode: (props.getProperty("DOC_FILENAME_MODE") || "title").toLowerCase()
  };

  var missing = [];
  if (!cfg.githubToken) missing.push("GITHUB_TOKEN");
  if (!cfg.owner) missing.push("GITHUB_OWNER");
  if (!cfg.repo) missing.push("GITHUB_REPO");
  if (!cfg.driveFolderId) missing.push("DRIVE_FOLDER_ID");

  if (missing.length > 0) {
    throw new Error("Missing Script Properties: " + missing.join(", "));
  }

  if (cfg.docFilenameMode !== "title" && cfg.docFilenameMode !== "doc_id") {
    throw new Error("Invalid DOC_FILENAME_MODE. Use 'title' or 'doc_id'.");
  }

  return cfg;
}

function getState_() {
  var raw;
  try {
    raw = getPropertyWithRetry_("SYNC_STATE_JSON");
  } catch (err) {
    // Transient Apps Script storage issues should not fail a whole sync run.
    Logger.log("Could not read SYNC_STATE_JSON; continuing with empty state. " + err);
    return {};
  }

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
  setPropertyWithRetry_("SYNC_STATE_JSON", JSON.stringify(stateObj));
}

function getScriptPropertiesWithRetry_() {
  var attempts = 4;
  var delayMs = 250;
  var lastErr;

  for (var i = 1; i <= attempts; i++) {
    try {
      return PropertiesService.getScriptProperties();
    } catch (err) {
      lastErr = err;
      if (i < attempts) {
        Utilities.sleep(delayMs);
        delayMs *= 2;
      }
    }
  }

  throw new Error("Failed to access Script Properties after retries: " + lastErr);
}

function getPropertyWithRetry_(key) {
  var attempts = 4;
  var delayMs = 250;
  var lastErr;

  for (var i = 1; i <= attempts; i++) {
    try {
      var props = getScriptPropertiesWithRetry_();
      return props.getProperty(key);
    } catch (err) {
      lastErr = err;
      if (i < attempts) {
        Utilities.sleep(delayMs);
        delayMs *= 2;
      }
    }
  }

  throw new Error("Failed reading Script Property '" + key + "' after retries: " + lastErr);
}

function setPropertyWithRetry_(key, value) {
  var attempts = 4;
  var delayMs = 250;
  var lastErr;

  for (var i = 1; i <= attempts; i++) {
    try {
      var props = getScriptPropertiesWithRetry_();
      props.setProperty(key, value);
      return;
    } catch (err) {
      lastErr = err;
      if (i < attempts) {
        Utilities.sleep(delayMs);
        delayMs *= 2;
      }
    }
  }

  throw new Error("Failed writing Script Property '" + key + "' after retries: " + lastErr);
}

function isSupportedSource_(name, mimeType) {
  if (/\.json$/i.test(name)) {
    return true;
  }

  if (mimeType === MimeType.GOOGLE_DOCS) {
    return true;
  }

  return false;
}

function readSourceText_(fileId, mimeType) {
  if (mimeType === MimeType.GOOGLE_DOCS) {
    return DocumentApp.openById(fileId).getBody().getText();
  }

  return DriveApp.getFileById(fileId).getBlob().getDataAsString("UTF-8");
}

function normalizeJsonText_(content, fileName) {
  var cleaned = content
    .replace(/\u201C|\u201D/g, '"')
    .replace(/\u2018|\u2019/g, "'")
    .trim();

  if (cleaned.indexOf("```") === 0) {
    cleaned = cleaned
      .replace(/^```(?:json)?\s*/i, "")
      .replace(/\s*```$/, "")
      .trim();
  }

  try {
    var parsed = JSON.parse(cleaned);
    return JSON.stringify(parsed, null, 2) + "\n";
  } catch (err) {
    throw new Error("Invalid JSON in file " + fileName + ": " + err);
  }
}

function buildTargetFileName_(name, fileId, mimeType, cfg) {
  if (mimeType === MimeType.GOOGLE_DOCS) {
    if (cfg.docFilenameMode === "title") {
      var baseName = name.replace(/\.json$/i, "");
      var safeTitle = sanitizeFileName_(baseName);
      if (!safeTitle) {
        return "doc-" + sanitizeFileName_(fileId) + ".json";
      }
      return safeTitle + ".json";
    }

    return "doc-" + sanitizeFileName_(fileId) + ".json";
  }

  if (/\.json$/i.test(name)) {
    return sanitizeFileName_(name);
  }

  return sanitizeFileName_(name) + ".json";
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
