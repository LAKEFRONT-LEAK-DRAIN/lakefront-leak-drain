import argparse
import base64
import json
import os
import re
from datetime import datetime
from urllib import error, parse, request

OWNER = "lakefrontleakanddrain-design"
REPO = "lakefront-leak-drain"
BRANCH = "main"
PENDING_TASKS_PATH = "hcp-automation/pending-tasks"


def sanitize_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", value.strip())


def build_payload(args: argparse.Namespace) -> dict:
    job_title = args.job_title or f"Estimate: {args.scope}"
    return {
        "first_name": args.first_name,
        "last_name": args.last_name,
        "street": args.street,
        "city": args.city,
        "state": args.state,
        "zip": args.zip_code,
        "phone": args.phone,
        "email": args.email,
        "job_title": job_title,
        "price_cents": args.price_cents,
        "requested_technician": args.requested_technician,
        "requested_schedule": args.requested_schedule,
        "service_summary": args.scope,
        "source": "lakefront_automation_cli",
    }


def github_request(url: str, token: str, method: str = "GET", body: dict | None = None) -> tuple[int, dict | str]:
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")

    req = request.Request(
        url,
        method=method,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )

    try:
        with request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, raw


def get_existing_sha(path: str, token: str) -> str | None:
    encoded_path = parse.quote(path)
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{encoded_path}?ref={BRANCH}"
    status, payload = github_request(url, token, "GET")

    if status == 404:
        return None
    if status < 200 or status > 299:
        raise RuntimeError(f"Failed to check existing file: HTTP {status} {payload}")

    return payload.get("sha")


def push_task_file(filename: str, content: str, token: str) -> None:
    path = f"{PENDING_TASKS_PATH}/{filename}"
    encoded_path = parse.quote(path)
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{encoded_path}"

    existing_sha = get_existing_sha(path, token)

    body = {
        "message": f"Add pending task: {filename}",
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": BRANCH,
    }
    if existing_sha:
        body["sha"] = existing_sha

    status, payload = github_request(url, token, "PUT", body)
    if status < 200 or status > 299:
        raise RuntimeError(f"Failed to push task file: HTTP {status} {payload}")

    commit_sha = payload.get("commit", {}).get("sha", "unknown")
    print(f"SUCCESS: {filename} pushed to {path}")
    print(f"Commit: {commit_sha}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create and push a pending-task JSON file to GitHub.")
    parser.add_argument("--first-name", required=True)
    parser.add_argument("--last-name", required=True)
    parser.add_argument("--phone", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--street", required=True)
    parser.add_argument("--city", required=True)
    parser.add_argument("--state", default="OH")
    parser.add_argument("--zip-code", required=True)
    parser.add_argument("--scope", required=True, help="Human-readable service summary")
    parser.add_argument("--requested-technician", default="")
    parser.add_argument("--requested-schedule", default="")
    parser.add_argument("--job-title", default="")
    parser.add_argument("--price-cents", type=int, default=100)
    parser.add_argument("--filename", default="", help="Optional filename override without path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN env var is required.")

    if args.filename:
        file_name = sanitize_filename(args.filename)
        if not file_name.lower().endswith(".json"):
            file_name += ".json"
    else:
        file_name = f"{sanitize_filename(args.first_name)}_{sanitize_filename(args.last_name)}.json"

    payload = build_payload(args)
    payload["created_at_utc"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    json_content = json.dumps(payload, indent=2) + "\n"

    push_task_file(file_name, json_content, token)


if __name__ == "__main__":
    main()