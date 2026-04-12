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


def normalize_optional_text(value: Any) -> str:
    text = str(value or "").strip()
    if not text or text.lower() in {"none", "null", "n/a", "na"}:
        return ""
    return text


def first_present(payload: Dict[str, Any], keys: list[str], default: Any = "") -> Any:
    for key in keys:
        if key in payload and payload[key] is not None:
            text = str(payload[key]).strip()
            if text:
                return payload[key]
    return default


def normalize_claim_number(value: Any) -> str:
    text = normalize_optional_text(value)
    if not text:
        return ""

    # Keep only letters, digits, dash, underscore for deterministic filenames and matching.
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "", text)
    return cleaned[:64]


def derive_job_title(payload: Dict[str, Any]) -> str:
    explicit_title = normalize_optional_text(payload.get("job_title", ""))
    if explicit_title:
        return explicit_title

    service_summary = normalize_optional_text(
        payload.get("service_summary", payload.get("scope", ""))
    )
    if not service_summary:
        return "General plumbing service"

    first_sentence = re.split(r"[.!?\n]", service_summary, maxsplit=1)[0].strip()
    if first_sentence:
        return first_sentence[:120]

    return "General plumbing service"


def parse_price_cents(value: Any) -> int:
    text = normalize_optional_text(value)
    if not text:
        return 0

    cleaned = text.replace("$", "").replace(",", "").strip().lower()
    if cleaned.endswith("cents"):
        cleaned = cleaned.replace("cents", "").strip()
    if cleaned.endswith("cent"):
        cleaned = cleaned.replace("cent", "").strip()

    try:
        return int(float(cleaned))
    except ValueError as exc:
        raise ValueError(f"Invalid price_cents value: {value}") from exc


def parse_payload_price_cents(payload: Dict[str, Any]) -> int:
    # Preferred explicit cents fields.
    cents_raw = first_present(
        payload,
        ["price_cents", "service_call_fee_cents", "service_fee_cents"],
        default="",
    )
    if str(cents_raw).strip():
        return parse_price_cents(cents_raw)

    # Dollar-style fee fields (e.g. "$75", "75", "85.00").
    dollars_raw = first_present(
        payload,
        ["service_call_fee", "service_fee", "fee", "price"],
        default="",
    )
    if str(dollars_raw).strip():
        return parse_dollars_to_cents(str(dollars_raw))

    return 0


def normalize_line_items(payload: Dict[str, Any], fallback_job_title: str, fallback_price_cents: int) -> list[Dict[str, Any]]:
    raw_items = payload.get("line_items", payload.get("lineItems", []))
    normalized: list[Dict[str, Any]] = []

    if isinstance(raw_items, list):
        for item in raw_items:
            if not isinstance(item, dict):
                continue

            name = normalize_optional_text(item.get("name", item.get("title", "")))
            if not name:
                continue

            unit_price = parse_price_cents(item.get("unit_price", item.get("price_cents", item.get("price", 0))))
            if unit_price < 0:
                raise ValueError("line_items unit_price cannot be negative")

            quantity_raw = item.get("quantity", 1)
            try:
                quantity = int(float(str(quantity_raw).strip() or "1"))
            except ValueError as exc:
                raise ValueError(f"Invalid line_items quantity value: {quantity_raw}") from exc

            if quantity <= 0:
                raise ValueError("line_items quantity must be at least 1")

            normalized.append(
                {
                    "name": name[:160],
                    "unit_price": unit_price,
                    "quantity": quantity,
                }
            )

    if normalized:
        return normalized

    return [
        {
            "name": fallback_job_title,
            "unit_price": fallback_price_cents,
            "quantity": 1,
        }
    ]


def parse_dollars_to_cents(value: str) -> int:
    cleaned = normalize_optional_text(value).replace("$", "").replace(",", "")
    if not cleaned:
        return 0
    try:
        return int(round(float(cleaned) * 100))
    except ValueError:
        return 0


def infer_job_title_from_issue(issue: str) -> str:
    issue_text = normalize_optional_text(issue)
    lowered = issue_text.lower()
    if "leak" in lowered:
        return "Plumbing Leak Repair"
    if "clog" in lowered or "drain" in lowered:
        return "Drain Service"
    if "water heater" in lowered:
        return "Water Heater Service"
    if issue_text:
        return issue_text[:120]
    return "General plumbing service"


def extract_choice_email_fields(raw_text: str, email_subject: str, email_from: str) -> Dict[str, Any]:
    lines = [line.strip() for line in raw_text.replace("\r", "").split("\n")]
    compact_lines = [line for line in lines if line]
    text = "\n".join(compact_lines)

    result: Dict[str, Any] = {}

    name_match = re.search(r"(?im)^\s*Name\s*:\s*(.+)$", text)
    if name_match:
        full_name = name_match.group(1).strip()
        parts = full_name.split()
        if parts:
            result["first_name"] = parts[0]
            result["last_name"] = " ".join(parts[1:]) if len(parts) > 1 else "Customer"

    address_line = ""
    city = ""
    state = "OH"
    zip_code = ""
    address_match = re.search(
        r"(?ims)^\s*Address\s*:\s*(.+?)\n\s*([A-Za-z .'-]+),\s*([A-Z]{2})\s*(\d{5}(?:-\d{4})?)",
        text,
    )
    if address_match:
        address_line = address_match.group(1).strip()
        city = address_match.group(2).strip()
        state = address_match.group(3).strip()
        zip_code = address_match.group(4).strip()
    if address_line:
        result["street"] = address_line
    if city:
        result["city"] = city
    if state:
        result["state"] = state
    if zip_code:
        result["zip"] = zip_code

    phone_match = re.search(r"(?im)^\s*Phone\s*:\s*([0-9()\-+ ]{7,})$", text)
    if phone_match:
        result["phone"] = phone_match.group(1).strip()

    email_match = re.search(r"(?im)^\s*Email\s*:\s*([^\s]+@[^\s]+)$", text)
    if email_match:
        result["email"] = email_match.group(1).strip()

    claim_match = re.search(r"(?im)^\s*Claim\s*Number\s*:\s*(.+)$", text)
    claim_number = normalize_claim_number(claim_match.group(1).strip() if claim_match else "")

    issue_match = re.search(r"(?is)\bIssue\s*:\s*(.+)$", text)
    issue = issue_match.group(1).strip() if issue_match else ""
    if issue:
        result["service_summary"] = issue[:1200]
        result["job_title"] = infer_job_title_from_issue(issue)

    service_fee_match = re.search(r"(?im)^\s*Service\s*Call\s*Fee\s*:\s*\$?\s*([0-9]+(?:\.[0-9]{1,2})?)", text)
    if service_fee_match:
        result["price_cents"] = parse_dollars_to_cents(service_fee_match.group(1))

    appointment_match = re.search(r"(?im)^\s*Appointment\s*:\s*(.+)$", text)
    time_slot_match = re.search(r"(?im)^\s*Time\s*Slot\s*:\s*(.+)$", text)
    appointment = appointment_match.group(1).strip() if appointment_match else ""
    time_slot = time_slot_match.group(1).strip() if time_slot_match else ""
    if appointment and time_slot:
        result["requested_schedule"] = f"{appointment} {time_slot}"
    elif appointment:
        result["requested_schedule"] = appointment
    elif time_slot:
        result["requested_schedule"] = time_slot

    if claim_number:
        result["claim_number"] = claim_number
        existing_summary = normalize_optional_text(result.get("service_summary", ""))
        if existing_summary:
            result["service_summary"] = f"Claim #{claim_number}. {existing_summary}"
        else:
            result["service_summary"] = f"Claim #{claim_number}"

    from_lower = email_from.lower()
    subject_lower = email_subject.lower()
    if "choicehomewarranty" in from_lower or "choice home warranty" in subject_lower:
        result["company_name"] = "Choice Home Warranty"

    result["source"] = "gemini_bridge_api"
    return result


def merge_payloads(preferred: Dict[str, Any], fallback: Dict[str, Any]) -> Dict[str, Any]:
    merged: Dict[str, Any] = dict(fallback)
    for key, value in preferred.items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, (list, dict)) and not value:
            continue
        merged[key] = value
    return merged


def parse_request_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    required = ["first_name", "last_name", "street", "city", "job_title"]
    for key in required:
        if key == "job_title":
            candidate_value = derive_job_title(payload)
        else:
            candidate_value = str(payload.get(key, "")).strip()
        if not candidate_value:
            raise ValueError(f"Missing required field: {key}")

    first_name = str(first_present(payload, ["first_name", "firstName"]))
    last_name = str(first_present(payload, ["last_name", "lastName"]))
    street = str(first_present(payload, ["street", "address", "address_1", "address1"]))
    city = str(first_present(payload, ["city", "town"]))
    state = str(first_present(payload, ["state", "province"], "OH")).strip()
    zip_code = str(first_present(payload, ["zip", "zip_code", "postal_code", "postal"], "")).strip()

    company_name = normalize_optional_text(
        payload.get("company_name", payload.get("company", ""))
    )
    if "choice home warranty" in company_name.lower():
        company_name = "Choice Home Warranty"

    result = {
        "first_name": first_name.strip(),
        "last_name": last_name.strip(),
        "company_name": company_name,
        "street": street.strip(),
        "city": city.strip(),
        "state": state,
        "zip": zip_code,
        "phone": normalize_optional_text(payload.get("phone", payload.get("mobile", ""))),
        "email": normalize_optional_text(payload.get("email", "")),
        "job_title": derive_job_title(payload),
        "price_cents": parse_payload_price_cents(payload),
        "requested_technician": normalize_optional_text(payload.get("requested_technician", "")),
        "requested_schedule": normalize_optional_text(payload.get("requested_schedule", "")),
        "service_summary": normalize_optional_text(
            payload.get("service_summary", payload.get("scope", derive_job_title(payload)))
        ),
        "source": str(payload.get("source", "gemini_bridge_api")).strip(),
        "claim_number": normalize_claim_number(
            first_present(payload, ["claim_number", "claimNumber", "claim_no", "claim"])
        ),
    }

    if result["price_cents"] < 0:
        raise ValueError("price_cents cannot be negative")

    if result["price_cents"] > 9_000_000_000_000:
        raise ValueError("price_cents is too large")

    result["line_items"] = normalize_line_items(
        payload,
        fallback_job_title=result["job_title"],
        fallback_price_cents=result["price_cents"],
    )

    result["created_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return result


def choose_filename(data: Dict[str, Any], requested_name: str = "") -> str:
    if requested_name.strip():
        base = sanitize_filename(requested_name)
    elif normalize_optional_text(data.get("claim_number", "")):
        base = sanitize_filename(f"claim_{data['claim_number']}")
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
    if not isinstance(payload, dict):
        return jsonify({"error": "JSON body required"}), 400

    raw_text = str(payload.get("text", payload.get("email_body", ""))).strip()
    if not raw_text:
        return jsonify({"error": "JSON body with 'text' or 'email_body' field required"}), 400

    email_subject = normalize_optional_text(payload.get("email_subject", ""))
    email_from = normalize_optional_text(payload.get("email_from", ""))
    email_received_at = normalize_optional_text(payload.get("email_received_at", ""))

    deterministic = extract_choice_email_fields(raw_text, email_subject, email_from)

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    parsed: Dict[str, Any] = {}

    if gemini_key:
        prompt = (
            "You are a JSON extraction assistant. Extract customer intake fields from the "
            "following home-warranty work-order email and return ONLY a valid JSON object "
            "with no markdown, no explanation, no code fences.\n\n"
            "Fields to extract (use exact key names):\n"
            "first_name, last_name, company_name, street, city, state, zip, phone, email, job_title, "
            "service_summary, price_cents, requested_schedule, requested_technician, line_items\n\n"
            "Rules:\n"
            "- The email may be written as labeled phrases, paragraphs, tables, or one field per line; use labels when present\n"
            "- job_title must never be \"None\" or blank; if only a service summary is given, infer a short job title from it\n"
            "- requested_schedule should contain the customer's preferred timing in plain English\n"
            "- requested_technician should contain the technician name or pro_ ID if one is given\n"
            "- line_items must be an array of objects with keys: name, unit_price, quantity\n"
            "- If only one scope item is present, return one line_items entry\n"
            "- state defaults to \"OH\" if not mentioned\n"
            "- price_cents defaults to 0 if not mentioned\n"
            "- If a dollar amount is given, convert dollars to cents (multiply by 100)\n"
            "- source should always be \"gemini_bridge_api\"\n"
            "- Return ONLY the JSON object, nothing else\n\n"
            f"Email From: {email_from or 'unknown'}\n"
            f"Email Subject: {email_subject or 'unknown'}\n"
            f"Email Received At: {email_received_at or 'unknown'}\n\n"
            f"Email Body:\n{raw_text}"
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
            assert isinstance(g_result, dict)
            extracted_text = g_result["candidates"][0]["content"]["parts"][0]["text"].strip()
            extracted_text = re.sub(r"^```[a-z]*\n?", "", extracted_text)
            extracted_text = re.sub(r"\n?```$", "", extracted_text).strip()
            parsed = json.loads(extracted_text)
        except Exception:
            parsed = {}

    combined = merge_payloads(parsed, deterministic)
    if not normalize_optional_text(combined.get("requested_schedule", "")):
        combined["requested_schedule"] = normalize_optional_text(payload.get("email_received_at", ""))

    try:
        normalized = parse_request_payload(combined)
        filename = choose_filename(normalized, str(combined.get("filename", "")))
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