import os
import random
import re
import json
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import escape as html_escape
from pathlib import Path
from xml.sax.saxutils import escape

import requests
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; LakefrontLeakDrainBot/1.0; +https://lakefrontleakanddrain.com)"
}

BASE_DIR = Path(__file__).resolve().parent
SITE_BASE_URL = "https://lakefrontleakanddrain.com"
VIDEO_FEED_FILE = os.environ.get("VIDEO_FEED_FILE", "Live_Video_Feed.xml").strip() or "Live_Video_Feed.xml"
VIDEO_FEED_PATH = BASE_DIR / VIDEO_FEED_FILE
VIDEO_PAGE_DIR = os.environ.get("VIDEO_PAGE_DIR", "live-video").strip() or "live-video"
DEFAULT_LINK = "https://lakefrontleakanddrain.com/"
DEFAULT_VIDEO = "https://lakefrontleakanddrain.com/logo-animated.mp4"
MAX_ITEMS = 20
RECENT_TITLE_LOOKBACK = 12
RECENT_VIDEO_LOOKBACK = 12
ALLOW_PEXELS_FALLBACK = os.environ.get("ALLOW_PEXELS_FALLBACK", "false").strip().lower() == "true"
ENFORCE_TEXT_VIDEO_ALIGNMENT = os.environ.get("ENFORCE_TEXT_VIDEO_ALIGNMENT", "true").strip().lower() == "true"
ALIGNMENT_MAX_CANDIDATES = 18
PEXELS_REFERENCE_QUERY = os.environ.get("PEXELS_REFERENCE_QUERY", "apartment plumbing").strip() or "apartment plumbing"
MULTIFAMILY_STRICT_STOCK_FILTER = os.environ.get("MULTIFAMILY_STRICT_STOCK_FILTER", "true").strip().lower() == "true"
MAX_VIDEO_WIDTH = int(os.environ.get("MAX_VIDEO_WIDTH", "1920"))
REQUIRE_VERTICAL_VIDEO = os.environ.get("REQUIRE_VERTICAL_VIDEO", "true").strip().lower() == "true"
USE_GEMINI_GENERATED_VIDEO = os.environ.get("USE_GEMINI_GENERATED_VIDEO", "false").strip().lower() == "true"
GEMINI_VIDEO_MODEL = os.environ.get("GEMINI_VIDEO_MODEL", "veo-3.1-generate-preview").strip() or "veo-3.1-generate-preview"
GEMINI_VIDEO_ASPECT_RATIO = os.environ.get("GEMINI_VIDEO_ASPECT_RATIO", "9:16").strip() or "9:16"
GEMINI_VIDEO_RESOLUTION = os.environ.get("GEMINI_VIDEO_RESOLUTION", "720p").strip() or "720p"
GEMINI_TEXT_MODEL = os.environ.get("GEMINI_TEXT_MODEL", "gemini-3-flash").strip() or "gemini-3-flash"
GEMINI_TEXT_FALLBACK_MODELS = [
    m.strip()
    for m in os.environ.get("GEMINI_TEXT_FALLBACK_MODELS", "gemini-2.5-flash").split(",")
    if m.strip()
]
GENERATED_VIDEO_SUBDIR = os.environ.get("GENERATED_VIDEO_SUBDIR", "generated").strip() or "generated"

CLEVELAND_LAT = 41.4993
CLEVELAND_LON = -81.6944
FORECAST_DAYS = 5
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
GENERATED_VIDEO_DIR = BASE_DIR / VIDEO_PAGE_DIR / GENERATED_VIDEO_SUBDIR
GENERATED_VIDEO_URL_PREFIX = f"{SITE_BASE_URL}/{VIDEO_PAGE_DIR}/{GENERATED_VIDEO_SUBDIR}"


def get_env_float(name, default):
    raw = (os.environ.get(name, "") or "").strip()
    if not raw:
        return float(default)
    try:
        return float(raw)
    except ValueError:
        return float(default)


ETHNICITY_BLEND_WEIGHTS = {
    "caucasian": get_env_float("CAST_WEIGHT_CAUCASIAN", 45),
    "african_american": get_env_float("CAST_WEIGHT_AFRICAN_AMERICAN", 20),
    "hispanic_latino": get_env_float("CAST_WEIGHT_HISPANIC_LATINO", 15),
    "asian": get_env_float("CAST_WEIGHT_ASIAN", 10),
    "middle_eastern_multiracial": get_env_float("CAST_WEIGHT_MIDDLE_EASTERN_MULTIRACIAL", 10),
}

PLUMBING_TERMS = [
    "drain",
    "sewer",
    "leak",
    "pipe",
    "commercial plumbing",
    "multifamily plumbing",
    "apartment plumbing",
    "property management plumbing",
    "apartment building pipes",
    "tenant turnover plumbing",
    "apartment restroom",
    "apartment kitchen sink",
    "apartment bathroom",
    "laundry room drain",
    "hydro jetting",
    "grease trap",
    "main sewer line",
    "main water line",
    "exterior cleanout",
    "toilet",
    "faucet",
    "backup",
    "jetting",
    "cleanout",
    "manifold",
    "meter",
    "inspection",
    "plumbing",
]

BLACKLIST_PEXELS_IDS = {
    "8987409",
    "4482373",
    "18104090",
    "36543596",
}

BAD_VIDEO_KEYWORDS = {
    "car",
    "auto",
    "mechanic",
    "vehicle",
    "motorcycle",
    "truck",
    "workout",
    "exercise",
    "sports",
    "gym",
    "dance",
    "music",
    "dj",
    "concert",
    "hvac",
    "electrical",
    "janitorial",
    "landscaping",
    "roofing",
    "boiler",
    "heating",
    "furnace",
}

GOOD_VIDEO_KEYWORDS = {
    "plumb",
    "drain",
    "sewer",
    "leak",
    "pipe",
    "water",
    "repair",
    "fix",
    "multifamily",
    "apartment",
    "tenant",
    "unit turn",
    "unit turnover",
    "turnover",
    "make ready",
    "property manager",
    "restroom",
    "hydro",
    "jet",
    "jetting",
    "grease",
    "trap",
    "cleanout",
    "main line",
    "manifold",
    "meter",
    "sink",
    "toilet",
    "faucet",
}

DISALLOWED_MULTIFAMILY_TITLE_TERMS = {
    "facility",
    "facilities",
    "fms",
    "office",
    "retail",
    "restaurant",
    "hospital",
    "warehouse",
    "commercial",
    "lifestyle",
}

MULTIFAMILY_VISUAL_HINTS = {
    "apartment",
    "apartments",
    "multifamily",
    "multi family",
    "condo",
    "condominium",
    "tenant",
    "unit turn",
    "turnover",
    "make ready",
    "corridor",
    "hallway",
    "laundry room",
    "leasing",
    "property management",
    "residential building",
}


def c_to_f(celsius):
    return (celsius * 9.0 / 5.0) + 32.0


def weather_code_label(code):
    labels = {
        0: "clear",
        1: "mainly clear",
        2: "partly cloudy",
        3: "overcast",
        45: "fog",
        48: "depositing rime fog",
        51: "light drizzle",
        53: "moderate drizzle",
        55: "dense drizzle",
        56: "light freezing drizzle",
        57: "dense freezing drizzle",
        61: "slight rain",
        63: "moderate rain",
        65: "heavy rain",
        66: "light freezing rain",
        67: "heavy freezing rain",
        71: "slight snow",
        73: "moderate snow",
        75: "heavy snow",
        77: "snow grains",
        80: "slight rain showers",
        81: "moderate rain showers",
        82: "violent rain showers",
        85: "slight snow showers",
        86: "heavy snow showers",
        95: "thunderstorm",
        96: "thunderstorm with slight hail",
        99: "thunderstorm with heavy hail",
    }
    return labels.get(int(code), "mixed conditions")


def fetch_cleveland_forecast():
    params = {
        "latitude": CLEVELAND_LAT,
        "longitude": CLEVELAND_LON,
        "timezone": "America/New_York",
        "forecast_days": FORECAST_DAYS,
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,windspeed_10m_max",
    }

    resp = requests.get(OPEN_METEO_URL, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    daily = data.get("daily") or {}

    dates = daily.get("time") or []
    weather_codes = daily.get("weather_code") or []
    temp_maxes = daily.get("temperature_2m_max") or []
    temp_mins = daily.get("temperature_2m_min") or []
    precip_sums = daily.get("precipitation_sum") or []
    precip_probs = daily.get("precipitation_probability_max") or []
    wind_maxes = daily.get("windspeed_10m_max") or []

    days = []
    for idx, date_str in enumerate(dates):
        try:
            days.append(
                {
                    "date": date_str,
                    "code": float(weather_codes[idx]),
                    "temp_max_c": float(temp_maxes[idx]),
                    "temp_min_c": float(temp_mins[idx]),
                    "precip_mm": float(precip_sums[idx]),
                    "precip_prob": float(precip_probs[idx]),
                    "wind_kmh": float(wind_maxes[idx]),
                }
            )
        except Exception:
            continue

    return days


def analyze_forecast_for_plumbing(days):
    if not days:
        return {
            "has_substantial_event": False,
            "event_notes": ["Forecast data unavailable."],
            "day_lines": ["- Forecast unavailable; use seasonal evergreen commercial plumbing topic."],
        }

    event_notes = []

    heavy_rain_days = [d for d in days if d["precip_mm"] >= 19.0 or (d["precip_mm"] >= 12.0 and d["precip_prob"] >= 75.0)]
    moderate_rain_days = [d for d in days if d["precip_mm"] >= 8.0 and d not in heavy_rain_days]
    freezing_days = [d for d in days if d["temp_min_c"] <= 0.0]
    freeze_thaw_days = [d for d in days if d["temp_min_c"] <= 0.0 and d["temp_max_c"] >= 4.0]
    high_wind_days = [d for d in days if d["wind_kmh"] >= 45.0]

    if heavy_rain_days:
        event_notes.append("Heavy rain risk: prioritize exterior cleanouts, main sewer line capacity, hydro jetting readiness, and overflow prevention.")
    elif moderate_rain_days:
        event_notes.append("Moderate rain risk: prioritize multifamily drain flow, exterior cleanout inspections, and common-area restroom uptime.")

    if freezing_days:
        event_notes.append("Freeze risk: prioritize exposed commercial water lines, meter assemblies, valves, and burst-pipe prevention.")

    if freeze_thaw_days:
        event_notes.append("Freeze-thaw swing: emphasize main water line stress checks, leak detection, and utility-room inspections.")

    if high_wind_days:
        event_notes.append("High wind risk: include outage-prep messaging for multifamily pumping systems, critical drains, and restroom continuity.")

    day_lines = []
    for d in days:
        max_f = round(c_to_f(d["temp_max_c"]))
        min_f = round(c_to_f(d["temp_min_c"]))
        day_lines.append(
            f"- {d['date']}: {weather_code_label(d['code'])}, high {max_f}F, low {min_f}F, precip {d['precip_mm']:.1f} mm, precip chance {d['precip_prob']:.0f}%, wind {d['wind_kmh']:.0f} km/h"
        )

    has_substantial_event = bool(heavy_rain_days or freezing_days or freeze_thaw_days or high_wind_days)

    if not event_notes:
        event_notes.append("No strong weather trigger in next 5 days; pick a seasonal evergreen commercial plumbing prevention topic.")

    return {
        "has_substantial_event": has_substantial_event,
        "event_notes": event_notes,
        "day_lines": day_lines,
    }


def build_forecast_context_block():
    try:
        days = fetch_cleveland_forecast()
        analysis = analyze_forecast_for_plumbing(days)
    except Exception as e:
        print(f"Forecast fetch failed: {e}")
        return (
            "Forecast unavailable due to API/network issue.\n"
            "- Use seasonal Cleveland commercial plumbing relevance as fallback.\n"
            "- Do not invent weather claims."
        )

    event_text = "\n".join(f"- {note}" for note in analysis["event_notes"])
    days_text = "\n".join(analysis["day_lines"]) or "- No day-level forecast data returned."
    event_flag = "YES" if analysis["has_substantial_event"] else "NO"

    return (
        f"Substantial plumbing-relevant weather event in next 5 days: {event_flag}\n"
        "Forecast analysis notes:\n"
        f"{event_text}\n"
        "Day-by-day forecast:\n"
        f"{days_text}"
    )


def safe_generate_content_text(prompt, model=None, attempts=3):
    preferred_model = (model or "").strip() or GEMINI_TEXT_MODEL
    model_chain = [preferred_model]
    for fallback_model in GEMINI_TEXT_FALLBACK_MODELS:
        if fallback_model not in model_chain:
            model_chain.append(fallback_model)

    last_error = None
    for active_model in model_chain:
        for attempt in range(1, attempts + 1):
            try:
                resp = client.models.generate_content(model=active_model, contents=prompt)
                return (resp.text or "").strip()
            except Exception as e:
                last_error = e
                print(f"Gemini generate_content failed (model={active_model}, attempt {attempt}/{attempts}): {e}")
                if attempt < attempts:
                    time.sleep(min(2 * attempt, 6))

    print(f"Gemini generate_content exhausted retries: {last_error}")
    return ""


def generate_topic(existing_titles):
    residential_markers = {
        "homeowner",
        "homeowners",
        "home",
        "homes",
        "residential",
        "kitchen",
        "basement",
        "sump",
        "hose bib",
        "water heater",
        "garbage disposal",
    }

    commercial_recent_titles = []
    for t in existing_titles:
        title_norm = normalize_text(t)
        if any(marker in title_norm for marker in residential_markers):
            continue
        commercial_recent_titles.append(t)

    recent_titles_text = "\n".join(f"- {t}" for t in commercial_recent_titles[:RECENT_TITLE_LOOKBACK]) or "- None"
    forecast_context = build_forecast_context_block()

    prompt = f"""
Invent ONE strong short-form VIDEO topic for Lakefront Leak & Drain in Cleveland, Ohio.

Avoid repeating or closely mimicking these recent titles:
{recent_titles_text}

Use this 5-day Cleveland weather context before deciding topic:
{forecast_context}

Rules:
- The topic MUST be 100% multifamily/commercial plumbing only for Cleveland, Ohio and MUST explicitly target Multifamily Property Managers, Regional Property Managers, and Maintenance Supervisors.
- Allowed service scope includes: apartment stack and branch drain backups, exterior main sewer line hydro jetting, multifamily main water line repairs, unit-turn plumbing readiness, common-area/laundry room drain issues, exterior cleanout issues, and plumbing-focused SLAs.
- STRICTLY FORBIDDEN: single-family homeowner advice, boiler or heating topics, HVAC, electrical, janitorial, landscaping, roofing, or any general facility maintenance not specific to plumbing.
- NEVER suggest non-plumbing content, general home improvement, or lifestyle topics.
- Tenant, apartment, and multifamily context is explicitly allowed.
- Favor seasonal relevance for Cleveland.
- If forecast indicates a substantial plumbing-relevant weather event, prioritize that event and create a prevention-focused topic tied to it.
- If no substantial weather event is present, use a strong evergreen seasonal plumbing prevention topic.
- Keep title concise and hooky for TikTok/Shorts.
- NEVER use these words in Title or video keyword: facility, facilities, FMS, office, retail, commercial.
- Output ONLY this format:
Title | video keyword
- video keyword should be 2 to 4 words describing a plumbing visual.
""".strip()

    text = safe_generate_content_text(prompt)

    try:
        title, search_keyword = [x.strip() for x in text.split("|", 1)]
    except Exception:
        title = text or "Cleveland Multifamily Main Line Service Alert"
        search_keyword = "multifamily plumbing"

    if contains_disallowed_multifamily_terms(title):
        print(f"Rejected topic title due to disallowed terminology: {title}")
        return "", ""

    return title, search_keyword


def create_slug(title):
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9 ]", "", slug)
    slug = slug.strip().replace(" ", "-")
    return slug or "video-tip"


def normalize_text(text):
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def contains_disallowed_multifamily_terms(text):
    normalized = normalize_text(text)
    if not normalized:
        return False

    for term in DISALLOWED_MULTIFAMILY_TITLE_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", normalized):
            return True
    return False


def has_multifamily_visual_hint(text):
    normalized = normalize_text(text)
    if not normalized:
        return False

    for hint in MULTIFAMILY_VISUAL_HINTS:
        if hint in normalized:
            return True
    return False


def build_video_queries(title, search_keyword):
    title_norm = normalize_text(title)
    hook = normalize_text(search_keyword) or "multifamily plumbing repair"

    matched_terms = [term for term in PLUMBING_TERMS if term in title_norm]
    strict_terms = " ".join(matched_terms[:2]).strip()

    neg_keywords = "-car -auto -mechanic -person -people -workout -exercise -sports -gym -music -hvac -electrical -janitorial -landscaping -roofing -boiler -heating"

    queries = []
    if strict_terms:
        queries.append(f"{strict_terms} plumber repair {neg_keywords}")
        queries.append(f"{strict_terms} plumbing {neg_keywords}")

    queries.extend(
        [
            f"{hook} multifamily plumbing {neg_keywords}",
            f"{hook} apartment plumbing {neg_keywords}",
            f"property management plumbing {neg_keywords}",
            f"apartment stack drain backup {neg_keywords}",
            f"unit turnover plumbing {neg_keywords}",
            f"laundry room drain plumbing {neg_keywords}",
            f"apartment bathroom plumbing {neg_keywords}",
            f"apartment kitchen drain plumbing {neg_keywords}",
            f"main sewer line jetting {neg_keywords}",
            f"multifamily main water line repair {neg_keywords}",
            f"apartment common area drain service {neg_keywords}",
            f"exterior cleanout plumbing {neg_keywords}",
            f"{hook} {neg_keywords}",
        ]
    )

    seen = set()
    unique_queries = []
    for q in queries:
        key = normalize_text(q)
        if key and key not in seen:
            seen.add(key)
            unique_queries.append(q.strip())
    return unique_queries


def is_plumbing_relevant(video_tags):
    if not video_tags:
        return False
    tags_lower = (video_tags or "").lower()

    if any(bad in tags_lower for bad in BAD_VIDEO_KEYWORDS):
        return False

    return any(good in tags_lower for good in GOOD_VIDEO_KEYWORDS)


def is_likely_non_plumbing(video_tags):
    tags_lower = (video_tags or "").lower()
    return any(bad in tags_lower for bad in BAD_VIDEO_KEYWORDS)


def is_platform_safe_video(width, height):
    try:
        video_width = int(width or 0)
        video_height = int(height or 0)
    except (TypeError, ValueError):
        return False

    if video_width <= 0 or video_height <= 0:
        return False

    if video_width > MAX_VIDEO_WIDTH:
        return False

    if REQUIRE_VERTICAL_VIDEO and video_height <= video_width:
        return False

    return True


def fetch_pexels_video_candidates(query):
    headers = {"Authorization": os.environ["PEXELS_API_KEY"]}
    resp = requests.get(
        "https://api.pexels.com/videos/search",
        params={"query": query, "per_page": 15, "orientation": "portrait", "size": "medium"},
        headers=headers,
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    videos = data.get("videos") or []

    candidates = []
    for v in videos:
        video_id = str(v.get("id", ""))
        if video_id in BLACKLIST_PEXELS_IDS:
            continue
        
        tags = v.get("tags", "")
        if not is_plumbing_relevant(tags):
            continue

        multifamily_score = 1 if has_multifamily_visual_hint(f"{tags} {query}") else 0
        if MULTIFAMILY_STRICT_STOCK_FILTER and multifamily_score == 0:
            continue

        thumb_url = (v.get("image") or "").strip()
        
        for vf in v.get("video_files") or []:
            if vf.get("file_type") == "video/mp4" and vf.get("link"):
                if not is_platform_safe_video(vf.get("width") or v.get("width"), vf.get("height") or v.get("height")):
                    continue
                candidates.append(
                    {
                        "video_url": vf.get("link"),
                        "thumb_url": thumb_url,
                        "id": f"pexels:{video_id}" if video_id else "",
                        "provider": "pexels",
                        "tags": str(tags or ""),
                        "source_query": query,
                        "multifamily_score": multifamily_score,
                    }
                )
    return candidates


def fetch_pixabay_video_candidates(query):
    params = {
        "q": query,
        "video_type": "all",
        "per_page": 20,
        "safesearch": "true",
        "order": "popular",
    }
    if "PIXABAY_API_KEY" in os.environ:
        params["key"] = os.environ["PIXABAY_API_KEY"]
    
    resp = requests.get(
        "https://pixabay.com/api/videos/",
        params=params,
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    videos = data.get("hits") or []

    candidates = []
    for v in videos:
        video_id = str(v.get("id", ""))
        if video_id in BLACKLIST_PEXELS_IDS:
            continue

        tags = v.get("tags", "")
        if is_likely_non_plumbing(tags):
            continue

        multifamily_score = 1 if has_multifamily_visual_hint(f"{tags} {query}") else 0
        if MULTIFAMILY_STRICT_STOCK_FILTER and multifamily_score == 0:
            continue

        # Pixabay tags can be sparse. For primary-source mode, allow neutral tags
        # and rely on bad-keyword rejection plus query quality.
        videos_obj = v.get("videos") or {}
        for quality_key in ["medium", "small", "large"]:
            video_data = videos_obj.get(quality_key)
            if video_data and video_data.get("url"):
                if not is_platform_safe_video(video_data.get("width"), video_data.get("height")):
                    continue
                candidates.append(
                    {
                        "video_url": video_data.get("url"),
                        "thumb_url": (video_data.get("thumbnail") or "").strip(),
                        "id": f"pixabay:{video_id}" if video_id else "",
                        "provider": "pixabay",
                        "tags": str(tags or ""),
                        "source_query": query,
                        "multifamily_score": multifamily_score,
                    }
                )
                break
    return candidates


def canonical_video_id(video_url):
    url = (video_url or "").strip().lower()
    if not url:
        return None

    pexels_match = re.search(r"/video-files/(\d+)/", url)
    if pexels_match:
        return f"pexels:{pexels_match.group(1)}"

    return f"url:{url}"


def extract_enclosure_url(item_text):
    enclosure_match = re.search(r'<enclosure\b[^>]*\burl="([^"]+)"', item_text, flags=re.S | re.I)
    return enclosure_match.group(1).strip() if enclosure_match else ""


def should_drop_item(item_text):
    enclosure_url = extract_enclosure_url(item_text)
    if not enclosure_url:
        return False

    if enclosure_url.strip().lower() == DEFAULT_VIDEO.lower():
        return True

    video_id = canonical_video_id(enclosure_url)
    if video_id and video_id.startswith("pexels:"):
        pexels_id = video_id.split(":", 1)[1]
        if pexels_id in BLACKLIST_PEXELS_IDS:
            return True

    return False


def extract_recent_video_ids(feed_text, lookback=RECENT_VIDEO_LOOKBACK):
    recent_ids = []
    for item in extract_items(feed_text):
        enclosure_match = re.search(r'<enclosure\b[^>]*\burl="([^"]+)"', item, flags=re.S | re.I)
        if enclosure_match:
            video_id = canonical_video_id(enclosure_match.group(1))
            if video_id:
                recent_ids.append(video_id)
        if len(recent_ids) >= lookback:
            break
    return set(recent_ids)


def safe_json_object(text):
    raw = (text or "").strip()
    if not raw:
        return {}

    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        pass

    fence_match = re.search(r"\{[\s\S]*\}", raw)
    if not fence_match:
        return {}

    try:
        data = json.loads(fence_match.group(0))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def generate_alignment_queries(title, description, cta, fallback_keyword):
    prompt = f"""
Create search queries to find stock video that visually matches this plumbing post.

Title: {title}
Description: {description}
CTA: {cta}

Return ONLY JSON:
{{"queries":["...","...","..."]}}

Rules:
- 5 to 8 queries
- each query 2 to 6 words
- ALL queries must describe multifamily plumbing visuals only: apartment stack lines, main sewer lines, main water lines, hydro jetting, common-area/laundry drains, exterior cleanouts, utility rooms, apartment unit plumbing activity
- STRICTLY FORBIDDEN terms or themes: single-family homeowner tips, HVAC, boiler, heating, electrical, janitorial, landscaping, roofing, lifestyle, or home decor visuals
- no punctuation except spaces
""".strip()

    try:
        text = safe_generate_content_text(prompt)
        data = safe_json_object(text)
        queries = data.get("queries") if isinstance(data, dict) else None
        if isinstance(queries, list):
            clean = []
            seen = set()
            for q in queries:
                text = normalize_text(str(q))
                if not text:
                    continue
                if text in seen:
                    continue
                seen.add(text)
                clean.append(text)
            if clean:
                return clean[:8]
    except Exception as e:
        print(f"Alignment query generation failed: {e}")

    fallback = [
        normalize_text(fallback_keyword) or "multifamily plumbing repair",
        "apartment plumbing",
        "unit turnover plumbing",
        "main sewer line",
        "hydro jetting drain",
        "apartment bathroom plumbing",
        "laundry room drain service",
    ]
    return [q for q in fallback if q]


def choose_best_aligned_candidate(title, description, cta, candidates):
    if not candidates:
        return None

    ranked_candidates = sorted(
        candidates,
        key=lambda c: int(c.get("multifamily_score", 0)),
        reverse=True,
    )
    shortlist = ranked_candidates[:ALIGNMENT_MAX_CANDIDATES]
    candidate_lines = []
    for idx, c in enumerate(shortlist, start=1):
        provider = c.get("provider", "unknown")
        tags = (c.get("tags") or "").strip() or "none"
        query = (c.get("source_query") or "").strip() or "none"
        mf_score = int(c.get("multifamily_score", 0))
        candidate_lines.append(f"{idx}. provider={provider}; multifamily_score={mf_score}; tags={tags}; query={query}")

    prompt = f"""
Pick the one best stock video candidate for this post.

Post:
- Title: {title}
- Description: {description}
- CTA: {cta}

Candidates:
{chr(10).join(candidate_lines)}

Return ONLY JSON: {{"choice": <number>, "reason": "short reason"}}
Use the candidate number only.
Prefer candidates with multifamily_score=1 and apartment-community context.
Reject any candidate that appears generic facilities-maintenance or office/retail focused.
""".strip()

    try:
        text = safe_generate_content_text(prompt)
        data = safe_json_object(text)
        choice = int(data.get("choice", 0))
        if 1 <= choice <= len(shortlist):
            picked = shortlist[choice - 1]
            print(f"Gemini alignment picked candidate #{choice}: {data.get('reason', 'no reason provided')}")
            return picked
    except Exception as e:
        print(f"Gemini candidate ranking failed: {e}")

    return random.choice(shortlist)


def pick_on_screen_ethnicity_guidance():
    weighted_guidance = [
        ("Primarily Caucasian adults in the scene", max(0.0, ETHNICITY_BLEND_WEIGHTS.get("caucasian", 0.0))),
        ("Primarily African American adults in the scene", max(0.0, ETHNICITY_BLEND_WEIGHTS.get("african_american", 0.0))),
        ("Primarily Hispanic/Latino adults in the scene", max(0.0, ETHNICITY_BLEND_WEIGHTS.get("hispanic_latino", 0.0))),
        ("Primarily Asian adults in the scene", max(0.0, ETHNICITY_BLEND_WEIGHTS.get("asian", 0.0))),
        (
            "Primarily Middle Eastern or multiracial adults in the scene",
            max(0.0, ETHNICITY_BLEND_WEIGHTS.get("middle_eastern_multiracial", 0.0)),
        ),
    ]

    total_weight = sum(weight for _, weight in weighted_guidance)
    if total_weight <= 0:
        return random.choice([label for label, _ in weighted_guidance])

    roll = random.random() * total_weight
    running = 0.0
    for label, weight in weighted_guidance:
        running += weight
        if roll <= running:
            return label

    return weighted_guidance[-1][0]


def pick_commercial_visual_scene():
    scenes = [
        "A cinematic establishing shot of a multifamily apartment mechanical room with exposed main water lines, pressure gauges, and meter assemblies under clean lighting.",
        "A wide shot of an apartment building exterior focusing on an access point for an underground main sewer cleanout near a multifamily entrance.",
        "A detailed close-up of high-pressure hydro-jetting equipment and hoses flushing a multifamily main drain line on a concrete service floor.",
        "A smooth tracking shot through a multifamily mechanical corridor with labeled plumbing manifolds, shutoff valves, and insulated pipe runs.",
        "A wide shot of a clean apartment common-area restroom highlighting sinks, flush valves, and drain performance with no people in frame.",
        "A close-up of an apartment kitchen sink drain and shutoff inspection during a unit turnover walkthrough.",
        "A unit-turnover bathroom inspection scene where a plumbing tech checks shutoffs, trap arms, and drain flow in an empty apartment.",
    ]
    return random.choice(scenes)


def build_gemini_video_prompt(title, description, cta):
    visual_scene = pick_commercial_visual_scene()
    prompt_parts = [
        "Create a realistic short social video for a Cleveland plumbing company serving multifamily property operations teams.",
        f"Topic: {title}.",
        f"Message: {description} {cta}".strip(),
        "Pacing requirement: create a fast, practical short-form clip with high energy and clear problem-to-fix progression.",
        "Duration target: 15 to 25 seconds.",
        "The scene must be 100% multifamily plumbing only and must never imply single-family homeowner service.",
        "The environment must clearly read as an apartment community: unit turnover interiors, apartment corridors, laundry/common plumbing spaces, or multifamily mechanical rooms.",
        "Continuity rule: EVERY shot from start to finish must stay inside the same apartment-community context and never drift into generic facilities-maintenance visuals.",
        "Continuity rule: maintain one consistent property type (multifamily apartments/condos) across the entire clip with no mid-video scene-type switching.",
        "Storyboard requirement: include at least one exterior apartment-building establishing shot and at least one in-unit apartment plumbing shot (kitchen, bathroom, or laundry).",
        "Shot sequence requirement: opening shot = apartment exterior; middle shots = in-unit/laundry/common-area plumbing work; closing shot = apartment context, not generic tools-only footage.",
        "Hook requirement: first 1 to 2 seconds must show an obvious plumbing issue signal (active drain backup, standing water, or urgent leak condition) in an apartment setting.",
        "Coverage requirement: use mostly close-up and medium-close shots of real plumbing actions: snaking, hydro-jet hose positioning, trap removal, shutoff checks, drain flow testing, and cleanup verification.",
        "Editing requirement: frequent cut cadence (about every 1 to 2 seconds), with clear visual progression from issue to fix to confirmed result.",
        "Camera language: practical handheld or shoulder-level movement preferred over cinematic sweeping shots.",
        "The building must look like apartments/condos, not office, retail, or industrial warehouse properties.",
        f"Primary scene direction: {visual_scene}",
        "Direction: use hands-on B-roll of actual plumbing work and environment context, not a talking-head format.",
        "No on-camera speaking people. No visible lip-syncing, interviews, or direct-to-camera presenters.",
        "Audio direction: narration must be voice-over only in clear English with a neutral United States accent.",
        "If any people appear incidentally, they must remain in the background and never speak on camera.",
        "Plumbing standards: all equipment, pipes, fixtures, and utility setups MUST strictly reflect United States multifamily plumbing norms and code-compliant service practices.",
        "Plumbing standards exclusions: absolutely no European-style plumbing fixtures and no boilers.",
        "Technician appearance: if a person is shown, they must appear as a certified multifamily plumbing technician using professional PPE.",
        "Uniform constraints: all uniforms, safety vests, and hard hats must be completely blank, with no names, no name tags, no identifying logos, and no company branding.",
        "Negative constraints: forbid text overlays, floating words, subtitles, watermarks, company logos, and brand marks anywhere in scene elements, walls, tools, clothing, or equipment.",
        "Scene exclusions: do NOT show office towers, retail storefronts, restaurants, hospitals, warehouses, or generic facilities-maintenance scenes unrelated to apartment communities.",
        "Scene exclusions: do NOT show detached single-family homes, suburban houses, or private homeowner interiors.",
        "Scene exclusions: do NOT transition to institutional maintenance environments, utility plants, or abstract industrial settings with no apartment cues.",
        "Scene exclusions: avoid long static establishing shots that do not include visible plumbing task context.",
        "Style exclusions: forbid cartoonish, illustrated, or animated styles.",
        "Style: realistic, clean, professional, multifamily B2B, vertical short-form social media clip.",
        "Composition: portrait framing, clear subject, smooth camera movement, no split screen.",
        "Do not include UI elements or on-screen interface chrome.",
    ]
    return " ".join(part for part in prompt_parts if part)


def generate_gemini_video_asset(title, description, cta, slug):
    GENERATED_VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    prompt = build_gemini_video_prompt(title, description, cta)

    config = types.GenerateVideosConfig(
        aspect_ratio=GEMINI_VIDEO_ASPECT_RATIO,
        resolution=GEMINI_VIDEO_RESOLUTION,
    )

    operation = client.models.generate_videos(
        model=GEMINI_VIDEO_MODEL,
        prompt=prompt,
        config=config,
    )

    while not operation.done:
        print("Waiting for Gemini video generation to complete...")
        time.sleep(10)
        operation = client.operations.get(operation)

    response = getattr(operation, "response", None)
    generated_videos = getattr(response, "generated_videos", None) or []
    if not generated_videos:
        raise RuntimeError("Gemini video generation completed without a video result")

    generated_video = generated_videos[0]
    client.files.download(file=generated_video.video)

    filename = f"{slug}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.mp4"
    output_path = GENERATED_VIDEO_DIR / filename
    generated_video.video.save(str(output_path))

    return f"{GENERATED_VIDEO_URL_PREFIX}/{filename}", ""


def get_video_url(title, search_keyword, recent_video_ids=None, description="", cta=""):
    video_url = DEFAULT_VIDEO
    thumb_url = ""
    queries = build_video_queries(title, search_keyword)
    recent_video_ids = recent_video_ids or set()
    gemini_failed = False

    if USE_GEMINI_GENERATED_VIDEO:
        try:
            gemini_video_url, gemini_thumb_url = generate_gemini_video_asset(title, description, cta, create_slug(title))
            print("Video generated with Gemini Veo")
            return gemini_video_url, gemini_thumb_url
        except Exception as e:
            print(f"Gemini video generation failed, trying stock fallback sources: {e}")
            gemini_failed = True

    print(f"Trying Pexels reference query first: {PEXELS_REFERENCE_QUERY}")
    try:
        pexels_candidates = fetch_pexels_video_candidates(PEXELS_REFERENCE_QUERY)
        if pexels_candidates:
            fresh_candidates = [c for c in pexels_candidates if canonical_video_id(c.get("video_url")) not in recent_video_ids]
            ranking_pool = fresh_candidates if fresh_candidates else pexels_candidates
            selected = choose_best_aligned_candidate(title, description, cta, ranking_pool)
            if selected:
                video_url = selected.get("video_url") or DEFAULT_VIDEO
                thumb_url = selected.get("thumb_url") or ""
                print("Video selected via Pexels reference query (topic-ranked)")
                if fresh_candidates:
                    print("Selected a fresh (non-recent) Pexels clip")
                else:
                    print("No fresh Pexels candidates found; reused an older clip")
                return video_url, thumb_url
    except Exception as e:
        print(f"Pexels reference query failed: {e}")

    if ENFORCE_TEXT_VIDEO_ALIGNMENT:
        alignment_queries = generate_alignment_queries(title, description, cta, search_keyword)
        combined_queries = []
        seen_query_keys = set()
        for q in alignment_queries + queries:
            q_key = normalize_text(q)
            if not q_key or q_key in seen_query_keys:
                continue
            seen_query_keys.add(q_key)
            combined_queries.append(q)

        all_candidates = []
        seen_candidate_ids = set()

        for query in combined_queries:
            try:
                for c in fetch_pixabay_video_candidates(query):
                    cid = canonical_video_id(c.get("video_url"))
                    if not cid or cid in seen_candidate_ids:
                        continue
                    seen_candidate_ids.add(cid)
                    all_candidates.append(c)
            except Exception as e:
                print(f"Pixabay search failed for '{query}': {e}")

        if ALLOW_PEXELS_FALLBACK:
            for query in combined_queries:
                try:
                    for c in fetch_pexels_video_candidates(query):
                        cid = canonical_video_id(c.get("video_url"))
                        if not cid or cid in seen_candidate_ids:
                            continue
                        seen_candidate_ids.add(cid)
                        all_candidates.append(c)
                except Exception as e:
                    print(f"Pexels search failed for '{query}': {e}")

        if all_candidates:
            fresh_candidates = [c for c in all_candidates if canonical_video_id(c.get("video_url")) not in recent_video_ids]
            ranking_pool = fresh_candidates if fresh_candidates else all_candidates
            selected = choose_best_aligned_candidate(title, description, cta, ranking_pool)
            if selected:
                print("Video selected in alignment mode")
                video_url = selected.get("video_url") or DEFAULT_VIDEO
                thumb_url = selected.get("thumb_url") or ""
                return video_url, thumb_url

        print("Alignment mode found no candidates. Using fallback selection logic.")

    print("Trying Pixabay first (primary source)...")
    pixabay_queries = ["plumbing"]

    seen_pixabay = set()
    for pq in pixabay_queries:
        q = pq.strip()
        q_key = normalize_text(q)
        if not q_key or q_key in seen_pixabay:
            continue
        seen_pixabay.add(q_key)
        try:
            candidates = fetch_pixabay_video_candidates(q)
            if candidates:
                fresh_candidates = [c for c in candidates if canonical_video_id(c.get("video_url")) not in recent_video_ids]
                chosen_pool = fresh_candidates if fresh_candidates else candidates
                selected = random.choice(chosen_pool)
                video_url = selected.get("video_url") or DEFAULT_VIDEO
                thumb_url = selected.get("thumb_url") or ""
                print(f"Video selected via Pixabay (primary) using query: {q}")
                if fresh_candidates:
                    print("Selected a fresh (non-recent) video clip")
                else:
                    print("No fresh candidates found; reused an older clip")
                return video_url, thumb_url
        except Exception as e:
            print(f"Pixabay search failed for '{q}': {e}")

    if not ALLOW_PEXELS_FALLBACK:
        print("Pixabay exhausted and Pexels fallback is disabled. Using default video fallback")
        if gemini_failed:
            raise RuntimeError("Gemini failed and Pexels fallback is disabled")
        return video_url, thumb_url

    print("Pixabay exhausted, trying Pexels fallback...")
    for query in queries:
        try:
            candidates = fetch_pexels_video_candidates(query)
            if candidates:
                fresh_candidates = [c for c in candidates if canonical_video_id(c.get("video_url")) not in recent_video_ids]
                chosen_pool = fresh_candidates if fresh_candidates else candidates
                selected = random.choice(chosen_pool)
                video_url = selected.get("video_url") or DEFAULT_VIDEO
                thumb_url = selected.get("thumb_url") or ""
                print(f"Video selected via Pexels (fallback) using query: {query}")
                if fresh_candidates:
                    print("Selected a fresh (non-recent) video clip")
                else:
                    print("No fresh candidates found for this query; reused an older clip")
                return video_url, thumb_url
        except Exception as e:
            print(f"Pexels search failed for '{query}': {e}")

    print("Using default video fallback")
    if gemini_failed:
        raise RuntimeError("Gemini failed and no stock candidate video was found")
    return video_url, thumb_url


def generate_video_page(title, slug, description_text, video_url, thumb_url):
    video_dir = BASE_DIR / VIDEO_PAGE_DIR
    if not video_dir.exists():
        video_dir.mkdir(parents=True, exist_ok=True)

    page_url = f"{SITE_BASE_URL}/{VIDEO_PAGE_DIR}/{slug}.html"
    safe_title = html_escape(title)
    safe_desc = html_escape(description_text)
    safe_video = html_escape(video_url)
    
    thumb_url = (thumb_url or "").strip() or "https://lakefrontleakanddrain.com/blog/logo_tmp.jpg"
    safe_thumb = html_escape(thumb_url)

    og_image_tag = f'<meta property="og:image" content="{safe_thumb}">'
    twitter_image_tag = f'<meta name="twitter:image" content="{safe_thumb}">'
    img_tag = ""

    html_content = f"""<!doctype html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
    <title>{safe_title} | Lakefront Leak & Drain</title>
    <meta name=\"description\" content=\"{safe_desc}\">
    <meta property=\"og:title\" content=\"{safe_title}\">
    <meta property=\"og:description\" content=\"{safe_desc}\">
    <meta property=\"og:type\" content=\"video.other\">
    <meta property=\"og:url\" content=\"{page_url}\">
    {og_image_tag}
    <meta property=\"og:video\" content=\"{safe_video}\">
    <meta property=\"og:video:secure_url\" content=\"{safe_video}\">
    <meta property=\"og:video:type\" content=\"video/mp4\">
    <meta property=\"og:video:width\" content=\"720\">
    <meta property=\"og:video:height\" content=\"1280\">
    <meta name=\"twitter:card\" content=\"summary_large_image\">
    <meta name=\"twitter:title\" content=\"{safe_title}\">
    <meta name=\"twitter:description\" content=\"{safe_desc}\">
    {twitter_image_tag}
</head>
<body>
    <main>
        <h1>{safe_title}</h1>
        <p>{safe_desc}</p>
        {img_tag}
        <video controls playsinline preload=\"metadata\" style=\"max-width:100%;height:auto;\">
            <source src=\"{safe_video}\" type=\"video/mp4\">
        </video>
    </main>
</body>
</html>
"""

    with open(video_dir / f"{slug}.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    return page_url


def generate_post_copy(title):
    forecast_context = build_forecast_context_block()

    prompt = f"""
Write short RSS-ready copy for this plumbing video:
{title}

Use this 5-day Cleveland weather context to drive urgency if a storm or freeze is coming:
{forecast_context}

Return ONLY valid JSON with keys:
headline
description
cta
hashtags

Rules:
- ALL content MUST directly relate to multifamily plumbing only: apartment stack drains, main sewer lines, main water lines, hydro jetting, common-area fixture maintenance, exterior cleanouts, or plumbing-specific service level agreements.
- Audience: Cleveland Multifamily Property Managers, Regional Managers, and Maintenance Supervisors hiring plumbing vendors.
- STRICTLY FORBIDDEN topics: single-family homeowner concerns, boilers, heating, HVAC, electrical, janitorial, landscaping, roofing, or any general facility maintenance not specific to plumbing.
- Tone: professional B2B, local, clear, accountable, urgent without hype.
- Value propositions must be present across description and/or cta: tech-forward dispatching with real-time updates, strict adherence to Not-To-Exceed (NTE) limits, and documented liability coverage.
- description must be exactly 2 short sentences grounded in the specific plumbing topic above. If there is a severe weather event, tie the description to the weather.
- cta must be one short, dynamic sentence for commercial decision-makers and should reinforce risk control, uptime, or SLA accountability.
- hashtags must be a single string of 3 to 5 relevant hashtags and MUST include #MultifamilyPlumbing #PropertyManagement #Cleveland.
- NEVER use these words in headline, description, or cta: facility, facilities, FMS, office, retail.
- No markdown.
""".strip()

    text = safe_generate_content_text(prompt)

    try:
        data = safe_json_object(text)
        headline = (data.get("headline") or title).strip()
        description = (data.get("description") or "").strip()
        cta = (data.get("cta") or "Protect apartment uptime with multifamily plumbing dispatch that honors NTE limits.").strip()
        hashtags = (data.get("hashtags") or "").strip()
    except Exception:
        headline = title
        description = "Multifamily plumbing emergencies in Cleveland can escalate quickly and disrupt tenants across multiple units. Get tech-forward dispatch with real-time updates, strict NTE control, and documented liability coverage."
        cta = "Protect your portfolio NTE limits and uptime with a multifamily plumbing partner built for property operations."
        hashtags = "#MultifamilyPlumbing #PropertyManagement #Cleveland #ApartmentMaintenance"

    if not description:
        description = "Multifamily plumbing emergencies in Cleveland can escalate quickly and disrupt tenants across multiple units. Get tech-forward dispatch with real-time updates, strict NTE control, and documented liability coverage."

    if not hashtags:
        hashtags = "#MultifamilyPlumbing #PropertyManagement #Cleveland #ApartmentMaintenance"

    required_hashtags = ["#MultifamilyPlumbing", "#PropertyManagement", "#Cleveland"]
    hashtag_tokens = [h for h in hashtags.split() if h.startswith("#")]
    normalized = {h.lower() for h in hashtag_tokens}
    for req in required_hashtags:
        if req.lower() not in normalized:
            hashtag_tokens.append(req)
    hashtags = " ".join(hashtag_tokens[:5]).strip() or "#MultifamilyPlumbing #PropertyManagement #Cleveland"

    if contains_disallowed_multifamily_terms(headline):
        headline = title

    if contains_disallowed_multifamily_terms(description):
        description = "Multifamily plumbing emergencies in Cleveland can escalate quickly and disrupt tenants across multiple units. Get tech-forward dispatch with real-time updates, strict NTE control, and documented liability coverage."

    if contains_disallowed_multifamily_terms(cta):
        cta = "Protect your portfolio NTE limits and uptime with a multifamily plumbing partner built for property operations."

    return headline, description, cta, hashtags


def make_description(description, cta, hashtags=""):
    return f"{description} {cta} {hashtags}".strip()


def local_file_path_from_site_url(url):
    normalized = (url or "").strip()
    site_prefix = SITE_BASE_URL.rstrip("/") + "/"
    if not normalized.startswith(site_prefix):
        return None

    rel = normalized[len(site_prefix):].strip("/")
    if not rel:
        return None

    candidate = (BASE_DIR / Path(rel)).resolve()
    try:
        candidate.relative_to(BASE_DIR.resolve())
    except ValueError:
        return None

    return candidate


def fetch_media_length(video_url):
    local_path = local_file_path_from_site_url(video_url)
    if local_path and local_path.exists() and local_path.is_file():
        try:
            return str(local_path.stat().st_size)
        except OSError:
            pass

    try:
        response = requests.head(
            video_url,
            allow_redirects=True,
            timeout=20,
            headers=REQUEST_HEADERS,
        )
        content_length = response.headers.get("Content-Length", "").strip()
        if content_length.isdigit():
            return content_length
    except requests.RequestException:
        pass

    try:
        response = requests.get(
            video_url,
            allow_redirects=True,
            timeout=20,
            headers={**REQUEST_HEADERS, "Range": "bytes=0-0"},
            stream=True,
        )
        content_range = response.headers.get("Content-Range", "")
        if "/" in content_range:
            total_size = content_range.split("/")[-1].strip()
            if total_size.isdigit():
                return total_size

        content_length = response.headers.get("Content-Length", "").strip()
        if content_length.isdigit():
            return content_length
    except requests.RequestException:
        pass

    return "0"


def build_thumbnail_url(video_url):
    if "cdn.pixabay.com/video/" in video_url and video_url.endswith(".mp4"):
        return video_url[:-4] + ".jpg"
    return "https://lakefrontleakanddrain.com/blog/logo_tmp.jpg"


def build_content_encoded(description_text, post_link, video_url):
    safe_post_link = html_escape(post_link, quote=True)
    safe_video_url = html_escape(video_url, quote=True)
    safe_description = html_escape(description_text)
    return (
        "<![CDATA["
        f"<p>{safe_description}</p>"
        f"<p><a href=\"{safe_post_link}\">Watch on Lakefront Leak &amp; Drain</a></p>"
        f"<video controls preload=\"metadata\" playsinline style=\"max-width:100%;height:auto;\">"
        f"<source src=\"{safe_video_url}\" type=\"video/mp4\">"
        "</video>"
        "]]>")


def build_item_xml(title, description_text, video_url, post_link):
    now = datetime.now(timezone.utc)
    pub_date = now.strftime("%a, %d %b %Y %H:%M:%S GMT")
    guid = f"lakefrontleakanddrain.com/{VIDEO_PAGE_DIR}/{now.strftime('%Y%m%d%H%M%S')}"

    safe_title = escape(title)
    safe_video = escape(video_url)
    safe_post_link = escape(post_link)
    media_length = fetch_media_length(video_url)
    content_encoded = build_content_encoded(description_text, post_link, video_url)
    thumbnail_url = build_thumbnail_url(video_url)
    safe_thumbnail = escape(thumbnail_url)

    return f"""    <item>
            <title><![CDATA[{title}]]></title>
                        <link>{safe_post_link}</link>
            <dc:creator><![CDATA[lakefrontleakanddrain]]></dc:creator>
      <guid isPermaLink=\"false\">{guid}</guid>
      <pubDate>{pub_date}</pubDate>
      <description><![CDATA[{description_text}]]></description>
            <content:encoded>{content_encoded}</content:encoded>
      <enclosure url=\"{safe_video}\" length=\"{media_length}\" type=\"video/mp4\" />
                <media:content url=\"{safe_video}\" fileSize=\"{media_length}\" medium=\"video\" type=\"video/mp4\" />
      <media:thumbnail url=\"{safe_thumbnail}\" />
    </item>"""


def extract_items(feed_text):
    return re.findall(r"<item>.*?</item>", feed_text, flags=re.S)


def extract_tag(item_text, tag_name):
    match = re.search(fr"<{tag_name}\b[^>]*>(.*?)</{tag_name}>", item_text, flags=re.S)
    return match.group(1).strip() if match else None


def strip_cdata(text):
    if not text:
        return ""
    m = re.match(r"<!\[CDATA\[(.*)\]\]>", text, flags=re.S)
    return m.group(1).strip() if m else text.strip()


def backfill_video_pages_and_links(feed_text):
    items = extract_items(feed_text)
    updated_feed = feed_text
    updated_count = 0

    for item in items:
        title_raw = extract_tag(item, "title") or ""
        if not title_raw:
            continue
        title = strip_cdata(title_raw)

        description_raw = extract_tag(item, "description") or ""
        description_text = strip_cdata(description_raw)

        video_url = extract_enclosure_url(item)
        if not video_url:
            continue

        slug = create_slug(title)
        page_url = f"{SITE_BASE_URL}/{VIDEO_PAGE_DIR}/{slug}.html"
        generate_video_page(title, slug, description_text, video_url, "")

        old_link_match = re.search(r"<link>(.*?)</link>", item, flags=re.S)
        if not old_link_match:
            continue
        old_link = old_link_match.group(1).strip()
        if old_link == page_url:
            continue

        updated_item = re.sub(r"<link>.*?</link>", f"<link>{page_url}</link>", item, count=1, flags=re.S)
        if updated_item != item:
            updated_feed = updated_feed.replace(item, updated_item, 1)
            updated_count += 1

    return updated_feed, updated_count


def extract_titles(feed_text):
    titles = []
    for item in extract_items(feed_text):
        title = extract_tag(item, "title")
        if title:
            titles.append(title)
    return titles


def title_exists(feed_text, title):
    existing_titles = {t.strip().lower() for t in extract_titles(feed_text)}
    return title.strip().lower() in existing_titles


def split_feed(feed_text):
    first_item_match = re.search(r"<item>", feed_text)
    end_match = re.search(r"</channel>\s*</rss>\s*$", feed_text, flags=re.S)

    if not end_match:
        raise ValueError(f"Could not find </channel></rss> in {VIDEO_FEED_FILE}")

    if first_item_match:
        header = feed_text[:first_item_match.start()]
        items_blob = feed_text[first_item_match.start() : end_match.start()]
    else:
        channel_close = feed_text.rfind("</channel>")
        if channel_close == -1:
            raise ValueError(f"Could not find </channel> in {VIDEO_FEED_FILE}")
        header = feed_text[:channel_close]
        items_blob = ""

    footer = feed_text[end_match.start() :]
    return header, items_blob, footer


def parse_pubdate(item_text):
    pub = extract_tag(item_text, "pubDate")
    if not pub:
        return None
    try:
        return parsedate_to_datetime(pub)
    except Exception:
        return None


def normalize_indent(item_text):
    item_text = item_text.strip()
    lines = item_text.splitlines()
    return "\n".join(("    " + line.lstrip()) if line.strip() else "" for line in lines)


def prune_and_sort_items(feed_text):
    items = extract_items(feed_text)
    records = []

    for idx, item in enumerate(items):
        if should_drop_item(item):
            continue
        records.append(
            {
                "item": normalize_indent(item),
                "title": (extract_tag(item, "title") or "").strip().lower(),
                "dt": parse_pubdate(item),
                "idx": idx,
            }
        )

    deduped = {}
    for rec in records:
        key = rec["title"] or f"__untitled_{rec['idx']}"
        existing = deduped.get(key)
        if existing is None:
            deduped[key] = rec
            continue

        old_dt = existing["dt"]
        new_dt = rec["dt"]
        if old_dt is None and new_dt is not None:
            deduped[key] = rec
        elif old_dt is not None and new_dt is not None and new_dt > old_dt:
            deduped[key] = rec

    final_records = list(deduped.values())
    final_records.sort(
        key=lambda r: (
            r["dt"] is not None,
            r["dt"].timestamp() if r["dt"] is not None else float("-inf"),
            -r["idx"],
        ),
        reverse=True,
    )

    final_records = final_records[:MAX_ITEMS]
    return [rec["item"] for rec in final_records]


def write_feed(feed_text):
    items = prune_and_sort_items(feed_text)
    header, _, footer = split_feed(feed_text)
    body = "\n\n".join(items)
    final_text = header.rstrip() + "\n\n" + body + "\n\n" + footer.lstrip()

    with open(VIDEO_FEED_PATH, "w", encoding="utf-8") as f:
        f.write(final_text)

    return final_text


def cleanup_generated_video_assets(feed_text):
    if not GENERATED_VIDEO_DIR.exists():
        return

    referenced_names = set()
    for item in extract_items(feed_text):
        video_url = extract_enclosure_url(item)
        if not video_url or not video_url.startswith(GENERATED_VIDEO_URL_PREFIX + "/"):
            continue
        referenced_names.add(video_url.rsplit("/", 1)[-1])

    for video_path in GENERATED_VIDEO_DIR.glob("*.mp4"):
        if video_path.name in referenced_names:
            continue
        try:
            video_path.unlink()
            print(f"Removed unreferenced generated video asset: {video_path.name}")
        except OSError as e:
            print(f"Could not remove stale generated video asset {video_path.name}: {e}")


def main():
    with open(VIDEO_FEED_PATH, "r", encoding="utf-8") as f:
        feed = f.read()

    feed, backfilled = backfill_video_pages_and_links(feed)
    if backfilled:
        print(f"Backfilled video pages/links for {backfilled} existing items")

    existing_titles = extract_titles(feed)

    title = ""
    search_keyword = ""
    last_candidate_title = ""
    last_candidate_keyword = ""
    for attempt in range(1, 6):
        candidate_title, candidate_keyword = generate_topic(existing_titles)
        last_candidate_title = (candidate_title or "").strip()
        last_candidate_keyword = (candidate_keyword or "").strip()
        if not candidate_title:
            print(f"Rejected candidate title on attempt {attempt}: disallowed terminology")
            continue
        if candidate_title and not title_exists(feed, candidate_title):
            title, search_keyword = candidate_title, candidate_keyword
            break
        print(f"Duplicate candidate title on attempt {attempt}: {candidate_title}")

    if not title:
        # Never no-op a successful workflow run: force uniqueness with timestamp suffix.
        base_title = last_candidate_title or "Cleveland Multifamily Plumbing SLA Alert"
        suffix = datetime.now(timezone.utc).strftime(" %Y-%m-%d %H%M UTC")
        title = (base_title + suffix).strip()
        search_keyword = last_candidate_keyword or "multifamily plumbing"
        print(f"Using forced-unique fallback title: {title}")

    recent_video_ids = extract_recent_video_ids(feed)

    headline = title
    description = ""
    cta = "Protect your multifamily NTE limits with plumbing dispatch you can track in real time."
    hashtags = "#MultifamilyPlumbing #PropertyManagement #Cleveland #ApartmentMaintenance"
    if ENFORCE_TEXT_VIDEO_ALIGNMENT:
        headline, description, cta, hashtags = generate_post_copy(title)

    video_url, thumb_url = get_video_url(
        title,
        search_keyword,
        recent_video_ids,
        description=description,
        cta=cta,
    )

    if (video_url or "").strip().lower() == DEFAULT_VIDEO.lower():
        raise RuntimeError("Resolved to default fallback video; aborting to avoid stale/no-op feed run")

    if not ENFORCE_TEXT_VIDEO_ALIGNMENT:
        headline, description, cta, hashtags = generate_post_copy(title)

    final_title = headline.strip() or title.strip()
    if contains_disallowed_multifamily_terms(final_title):
        final_title = title.strip()
        print(f"Final headline reset to topic title due to disallowed terminology: {final_title}")

    if title_exists(feed, final_title):
        # Keep the run productive even when Gemini copy generation collides.
        suffix = datetime.now(timezone.utc).strftime(" %Y-%m-%d %H%M UTC")
        final_title = (final_title + suffix).strip()
        print(f"Adjusted duplicate headline to unique title: {final_title}")

    description_text = make_description(description, cta, hashtags)
    slug = create_slug(final_title)
    post_link = generate_video_page(final_title, slug, description_text, video_url, thumb_url)
    new_item = build_item_xml(final_title, description_text, video_url, post_link)

    header, items_blob, footer = split_feed(feed)
    updated_feed = header + new_item + "\n\n" + items_blob.lstrip() + footer
    final_feed = write_feed(updated_feed)
    cleanup_generated_video_assets(final_feed)

    print(f"Added new video item at top: {final_title}")


if __name__ == "__main__":
    main()
