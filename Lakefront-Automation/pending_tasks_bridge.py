import base64
import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, Tuple
from urllib import error, parse, request

from flask import Flask, jsonify, request as flask_request


app = Flask(__name__)


def env_required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def sanitize_filename(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]", "_", value.strip())
    sanitized = re.sub(r"_+", "_", sanitized).strip("_")
    return sanitized


def parse_request_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    required = ["first_name", "last_name", "street", "city", "job_title"]
    for key in required:
        if not str(payload.get(key, "")).strip():
            raise ValueError(f"Missing required field: {key}")

    result = {
        "first_name": str(payload["first_name"]).strip(),
        "last_name": str(payload["last_name"]).strip(),
        "company_name": str(payload.get("company_name", payload.get("company", ""))).strip(),
        "street": str(payload["street"]).strip(),
        "city": str(payload["city"]).strip(),
        "state": str(payload.get("state", "OH")).strip(),
        "zip": str(payload.get("zip", payload.get("zip_code", ""))).strip(),
        "phone": str(payload.get("phone", "")).strip(),
        "email": str(payload.get("email", "")).strip(),
        "job_title": str(payload["job_title"]).strip(),
        "price_cents": int(payload.get("price_cents", 100)),
        "requested_technician": str(payload.get("requested_technician", "")).strip(),
        "requested_schedule": str(payload.get("requested_schedule", "")).strip(),
        "service_summary": str(payload.get("service_summary", payload.get("scope", payload["job_title"]))).strip(),
        "source": str(payload.get("source", "gemini_bridge_api")).strip(),
    }

    if result["price_cents"] <= 0:
        raise ValueError("price_cents must be greater than 0")

    if result["price_cents"] > 9_000_000_000_000:
        raise ValueError("price_cents is too large")

    result["created_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return result


def choose_filename(data: Dict[str, Any], requested_name: str = "") -> str:
    if requested_name.strip():
        base = sanitize_filename(requested_name)
    else:
        base = sanitize_filename(f"{data['first_name']}_{data['last_name']}")

    if not base:
        base = f"task_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    if not base.lower().endswith(".json"):
        base += ".json"

    return base


def github_request(
    method: str,
    url: str,
    token: str,
    body: Dict[str, Any] | None = None,
) -> Tuple[int, Dict[str, Any] | str]:
    raw_body = None
    if body is not None:
        raw_body = json.dumps(body).encode("utf-8")

    req = request.Request(
        url,
        method=method,
        data=raw_body,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )

    try:
        with request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode("utf-8")
            if not text:
                return resp.status, {}
            return resp.status, json.loads(text)
    except error.HTTPError as exc:
        text = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(text)
        except json.JSONDecodeError:
            return exc.code, text


def get_existing_sha(owner: str, repo: str, branch: str, token: str, path: str) -> str | None:
    encoded_path = parse.quote(path)
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{encoded_path}?ref={parse.quote(branch)}"
    status, payload = github_request("GET", url, token)
    if status == 404:
        return None
    if status < 200 or status > 299:
        raise RuntimeError(f"GitHub lookup failed ({status}): {payload}")
    assert isinstance(payload, dict)
    return payload.get("sha")


def upsert_pending_task(data: Dict[str, Any], filename: str) -> Dict[str, Any]:
    token = env_required("GITHUB_TOKEN")
    owner = os.getenv("GITHUB_OWNER", "lakefrontleakanddrain-design").strip()
    repo = os.getenv("GITHUB_REPO", "lakefront-leak-drain").strip()
    branch = os.getenv("GITHUB_BRANCH", "main").strip()
    pending_path = os.getenv("GITHUB_PENDING_TASKS_PATH", "hcp-automation/pending-tasks").strip().strip("/")

    file_path = f"{pending_path}/{filename}"
    encoded_path = parse.quote(file_path)
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{encoded_path}"

    existing_sha = get_existing_sha(owner, repo, branch, token, file_path)
    content = json.dumps(data, indent=2) + "\n"

    payload = {
        "message": f"Bridge: add pending task {filename}",
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": branch,
    }
    if existing_sha:
        payload["sha"] = existing_sha

    status, result = github_request("PUT", url, token, payload)
    if status < 200 or status > 299:
        raise RuntimeError(f"GitHub write failed ({status}): {result}")

    assert isinstance(result, dict)
    commit_sha = (result.get("commit") or {}).get("sha", "")
    return {
        "file_path": file_path,
        "commit_sha": commit_sha,
    }


def authorize_or_401() -> Tuple[bool, Any]:
    expected = os.getenv("BRIDGE_API_KEY", "").strip()
    if not expected:
        return False, (jsonify({"error": "Server misconfigured: BRIDGE_API_KEY missing"}), 500)

    provided = flask_request.headers.get("x-bridge-key", "").strip()
    if provided != expected:
        return False, (jsonify({"error": "Unauthorized"}), 401)
    return True, None


@app.get("/healthz")
def healthz() -> Any:
    return jsonify({"ok": True})


@app.post("/intake")
def intake_from_text() -> Any:
    ok, err = authorize_or_401()
    if not ok:
        return err

    payload = flask_request.get_json(silent=True)
    if not isinstance(payload, dict) or not str(payload.get("text", "")).strip():
        return jsonify({"error": "JSON body with 'text' field required"}), 400

    raw_text = str(payload["text"]).strip()

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not gemini_key:
        return jsonify({"error": "Server misconfigured: GEMINI_API_KEY missing"}), 500

    prompt = (
        "You are a JSON extraction assistant. Extract customer intake fields from the "
        "following spoken note and return ONLY a valid JSON object with no markdown, "
        "no explanation, no code fences.\n\n"
        "Fields to extract (use exact key names):\n"
        "first_name, last_name, company_name, street, city, state, zip, phone, email, job_title, "
        "service_summary, price_cents\n\n"
        "Rules:\n"
        "- state defaults to \"OH\" if not mentioned\n"
        "- price_cents defaults to 100 if not mentioned, otherwise convert dollars to "
        "cents (multiply by 100)\n"
        "- source should always be \"gemini_bridge_api\"\n"
        "- Return ONLY the JSON object, nothing else\n\n"
        f"Spoken note:\n{raw_text}"
    )

    gemini_url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={gemini_key}"
    )
    gemini_body = {"contents": [{"parts": [{"text": prompt}]}]}
    raw_body = json.dumps(gemini_body).encode("utf-8")
    req = request.Request(
        gemini_url,
        method="POST",
        data=raw_body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with request.urlopen(req, timeout=30) as resp:
            g_result = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        g_result = json.loads(exc.read().decode("utf-8"))
        return jsonify({"error": f"Gemini API error: {g_result}"}), 500

    try:
        assert isinstance(g_result, dict)
        extracted_text = g_result["candidates"][0]["content"]["parts"][0]["text"].strip()
        extracted_text = re.sub(r"^```[a-z]*\n?", "", extracted_text)
        extracted_text = re.sub(r"\n?```$", "", extracted_text).strip()
        parsed = json.loads(extracted_text)
    except Exception as exc:
        return jsonify({"error": f"Gemini parse failed: {exc}", "raw": g_result}), 500

    try:
        normalized = parse_request_payload(parsed)
        filename = choose_filename(normalized, str(parsed.get("filename", "")))
        pushed = upsert_pending_task(normalized, filename)
        return jsonify({
            "ok": True,
            "filename": filename,
            "file_path": pushed["file_path"],
            "commit_sha": pushed["commit_sha"],
        })
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.post("/create-pending-task")
def create_pending_task() -> Any:
    ok, err = authorize_or_401()
    if not ok:
        return err

    payload = flask_request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "JSON body required"}), 400

    try:
        normalized = parse_request_payload(payload)
        filename = choose_filename(normalized, str(payload.get("filename", "")))
        pushed = upsert_pending_task(normalized, filename)
        return jsonify({
            "ok": True,
            "filename": filename,
            "file_path": pushed["file_path"],
            "commit_sha": pushed["commit_sha"],
        })
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)