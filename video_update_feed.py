import os
import random
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import escape as html_escape
from pathlib import Path
from xml.sax.saxutils import escape

import requests
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; LakefrontLeakDrainBot/1.0; +https://lakefrontleakanddrain.com)"
}

BASE_DIR = Path(__file__).resolve().parent
SITE_BASE_URL = "https://lakefrontleakanddrain.com"
VIDEO_FEED_PATH = BASE_DIR / "video_feed.xml"
DEFAULT_LINK = "https://lakefrontleakanddrain.com/"
DEFAULT_VIDEO = "https://lakefrontleakanddrain.com/logo-animated.mp4"
MAX_ITEMS = 20
RECENT_TITLE_LOOKBACK = 12
RECENT_VIDEO_LOOKBACK = 12
ALLOW_PEXELS_FALLBACK = os.environ.get("ALLOW_PEXELS_FALLBACK", "false").strip().lower() == "true"
MAX_VIDEO_WIDTH = int(os.environ.get("MAX_VIDEO_WIDTH", "1920"))
REQUIRE_VERTICAL_VIDEO = os.environ.get("REQUIRE_VERTICAL_VIDEO", "true").strip().lower() == "true"
CLEVELAND_LAT = 41.4993
CLEVELAND_LON = -81.6944
FORECAST_DAYS = 5
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

PLUMBING_TERMS = [
    "drain",
    "sewer",
    "leak",
    "pipe",
    "sump",
    "water heater",
    "toilet",
    "faucet",
    "backup",
    "flood",
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
    "house",
    "home",
    "bathroom",
    "kitchen",
    "basement",
    "sink",
    "toilet",
    "faucet",
    "heater",
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
            "day_lines": ["- Forecast unavailable; use seasonal evergreen plumbing topic."],
        }

    event_notes = []

    heavy_rain_days = [d for d in days if d["precip_mm"] >= 19.0 or (d["precip_mm"] >= 12.0 and d["precip_prob"] >= 75.0)]
    moderate_rain_days = [d for d in days if d["precip_mm"] >= 8.0 and d not in heavy_rain_days]
    freezing_days = [d for d in days if d["temp_min_c"] <= 0.0]
    freeze_thaw_days = [d for d in days if d["temp_min_c"] <= 0.0 and d["temp_max_c"] >= 4.0]
    high_wind_days = [d for d in days if d["wind_kmh"] >= 45.0]

    if heavy_rain_days:
        event_notes.append("Heavy rain risk: prioritize sump pump, drainage, backups, and main line prevention.")
    elif moderate_rain_days:
        event_notes.append("Moderate rain risk: consider drain clogs, gutter/downspout tie-ins, and sump readiness.")

    if freezing_days:
        event_notes.append("Freeze risk: prioritize frozen pipes, hose bibs, and burst-pipe prevention.")

    if freeze_thaw_days:
        event_notes.append("Freeze-thaw swing: emphasize crack/leak checks and pipe stress points.")

    if high_wind_days:
        event_notes.append("High wind risk: include outage-prep messaging for sump pumps and basement water management.")

    day_lines = []
    for d in days:
        max_f = round(c_to_f(d["temp_max_c"]))
        min_f = round(c_to_f(d["temp_min_c"]))
        day_lines.append(
            f"- {d['date']}: {weather_code_label(d['code'])}, high {max_f}F, low {min_f}F, precip {d['precip_mm']:.1f} mm, precip chance {d['precip_prob']:.0f}%, wind {d['wind_kmh']:.0f} km/h"
        )

    has_substantial_event = bool(heavy_rain_days or freezing_days or freeze_thaw_days or high_wind_days)

    if not event_notes:
        event_notes.append("No strong weather trigger in next 5 days; pick seasonal evergreen prevention topic.")

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
            "- Use seasonal Cleveland plumbing relevance as fallback.\n"
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


def generate_topic(existing_titles):
    recent_titles_text = "\n".join(f"- {t}" for t in existing_titles[:RECENT_TITLE_LOOKBACK]) or "- None"
    forecast_context = build_forecast_context_block()

    prompt = f"""
Invent ONE strong short-form VIDEO topic for Lakefront Leak & Drain in Cleveland, Ohio.

Avoid repeating or closely mimicking these recent titles:
{recent_titles_text}

Use this 5-day Cleveland weather context before deciding topic:
{forecast_context}

Rules:
- Make it specific to homeowners, drains, sewer lines, leaks, sump pumps, frozen pipes, water heaters, inspections, backups, or plumbing emergencies.
- Favor seasonal relevance for Cleveland.
- If forecast indicates a substantial plumbing-relevant weather event, prioritize that event and create a prevention-focused topic tied to it.
- If no substantial weather event is present, use a strong evergreen seasonal plumbing prevention topic.
- Keep title concise and hooky for TikTok/Shorts.
- Output ONLY this format:
Title | video keyword
- video keyword should be 2 to 4 words.
""".strip()

    resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    text = (resp.text or "").strip()

    try:
        title, search_keyword = [x.strip() for x in text.split("|", 1)]
    except Exception:
        title = text or "Cleveland Plumbing Emergency Warning Signs"
        search_keyword = "plumbing repair"

    return title, search_keyword


def create_slug(title):
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9 ]", "", slug)
    slug = slug.strip().replace(" ", "-")
    return slug or "video-tip"


def normalize_text(text):
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def build_video_queries(title, search_keyword):
    title_norm = normalize_text(title)
    hook = normalize_text(search_keyword) or "plumbing repair"

    matched_terms = [term for term in PLUMBING_TERMS if term in title_norm]
    strict_terms = " ".join(matched_terms[:2]).strip()

    neg_keywords = "-car -auto -mechanic -person -people -workout -exercise -sports -gym -music"

    queries = []
    if strict_terms:
        queries.append(f"{strict_terms} plumber repair {neg_keywords}")
        queries.append(f"{strict_terms} plumbing {neg_keywords}")

    queries.extend(
        [
            f"{hook} plumbing repair {neg_keywords}",
            f"{hook} plumber {neg_keywords}",
            f"drain cleaning plumber {neg_keywords}",
            f"pipe leak repair {neg_keywords}",
            f"sewer line repair {neg_keywords}",
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

    strict_candidates = []
    neutral_candidates = []
    for v in videos:
        video_id = str(v.get("id", ""))
        if video_id in BLACKLIST_PEXELS_IDS:
            continue
        
        tags = v.get("tags", "")
        if is_likely_non_plumbing(tags):
            continue

        is_strict_match = is_plumbing_relevant(tags)

        thumb_url = (v.get("image") or "").strip()
        
        for vf in v.get("video_files") or []:
            if vf.get("file_type") == "video/mp4" and vf.get("link"):
                if not is_platform_safe_video(vf.get("width") or v.get("width"), vf.get("height") or v.get("height")):
                    continue
                target_list = strict_candidates if is_strict_match else neutral_candidates
                target_list.append(
                    {
                        "video_url": vf.get("link"),
                        "thumb_url": thumb_url,
                        "id": f"pexels:{video_id}" if video_id else "",
                    }
                )
    # Prefer strong plumbing-tag matches, then fall back to neutral-but-safe clips.
    return strict_candidates or neutral_candidates


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


def get_video_url(title, search_keyword, recent_video_ids=None):
    video_url = DEFAULT_VIDEO
    thumb_url = ""
    queries = build_video_queries(title, search_keyword)
    recent_video_ids = recent_video_ids or set()

    print("Trying Pixabay first (primary source)...")
    pixabay_queries = [
        search_keyword,
        "plumbing",
        "drain repair",
        "sump pump",
        "leaking pipe",
    ]

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
        raise RuntimeError("No stock candidates found from Pixabay and Pexels fallback is disabled")

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
    raise RuntimeError("No stock candidates found from Pixabay/Pexels")


def generate_video_page(title, slug, description_text, video_url, thumb_url):
    video_dir = BASE_DIR / "video"
    if not video_dir.exists():
        video_dir.mkdir(parents=True, exist_ok=True)

    page_url = f"{SITE_BASE_URL}/video/{slug}.html"
    safe_title = html_escape(title)
    safe_desc = html_escape(description_text)
    safe_video = html_escape(video_url)
    
    # Build thumbnail URL if not provided
    if not thumb_url:
        thumb_url = build_thumbnail_url(video_url)
    safe_thumb = html_escape(thumb_url)

    og_image_tag = f'<meta property="og:image" content="{safe_thumb}">' if safe_thumb else ""
    twitter_image_tag = f'<meta name="twitter:image" content="{safe_thumb}">' if safe_thumb else ""

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
    <meta name=\"twitter:card\" content=\"summary_large_image\">
    <meta name=\"twitter:title\" content=\"{safe_title}\">
    <meta name=\"twitter:description\" content=\"{safe_desc}\">
    {twitter_image_tag}
</head>
<body>
    <main>
        <h1>{safe_title}</h1>
        <p>{safe_desc}</p>
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
    prompt = f"""
Write short RSS-ready copy for this video title:
{title}

Return ONLY valid JSON with keys:
headline
description
cta

Rules:
- Audience: Cleveland homeowners.
- Tone: helpful, local, clear, urgent but not spammy.
- description must be exactly 2 short sentences.
- cta must be one short sentence.
- No markdown.
""".strip()

    resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    text = (resp.text or "").strip()

    import json

    try:
        data = json.loads(text)
        headline = (data.get("headline") or title).strip()
        description = (data.get("description") or "").strip()
        cta = (data.get("cta") or "Call or book Lakefront Leak & Drain.").strip()
    except Exception:
        headline = title
        description = "Cleveland plumbing issues can escalate fast when warning signs are ignored. Learn what to watch for so you can act early and avoid bigger damage."
        cta = "Call or book Lakefront Leak & Drain."

    if not description:
        description = "Cleveland plumbing issues can escalate fast when warning signs are ignored. Learn what to watch for so you can act early and avoid bigger damage."

    return headline, description, cta


def make_description(description, cta):
    return f"{description} {cta}".strip()


def fetch_media_length(video_url):
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
    return "https://lakefrontleakanddrain.com/logo.jpg"


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
    guid = f"lakefrontleakanddrain.com/video/{now.strftime('%Y%m%d%H%M%S')}"

    safe_title = escape(title)
    safe_video = escape(video_url)
    safe_post_link = escape(post_link)
    media_length = fetch_media_length(video_url)
    thumbnail_url = escape(build_thumbnail_url(video_url))
    content_encoded = build_content_encoded(description_text, post_link, video_url)

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
            <media:thumbnail url=\"{thumbnail_url}\" />
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
        page_url = f"{SITE_BASE_URL}/video/{slug}.html"
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
        raise ValueError("Could not find </channel></rss> in video_feed.xml")

    if first_item_match:
        header = feed_text[:first_item_match.start()]
        items_blob = feed_text[first_item_match.start() : end_match.start()]
    else:
        channel_close = feed_text.rfind("</channel>")
        if channel_close == -1:
            raise ValueError("Could not find </channel> in video_feed.xml")
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
        if candidate_title and not title_exists(feed, candidate_title):
            title, search_keyword = candidate_title, candidate_keyword
            break
        print(f"Duplicate candidate title on attempt {attempt}: {candidate_title}")

    if not title:
        base_title = last_candidate_title or "Cleveland Plumbing Prevention Alert"
        suffix = datetime.now(timezone.utc).strftime(" %Y-%m-%d %H%M UTC")
        title = (base_title + suffix).strip()
        search_keyword = last_candidate_keyword or "plumbing prevention"
        print(f"Using forced-unique fallback title: {title}")

    recent_video_ids = extract_recent_video_ids(feed)
    video_url, thumb_url = get_video_url(title, search_keyword, recent_video_ids)

    if (video_url or "").strip().lower() == DEFAULT_VIDEO.lower():
        raise RuntimeError("Resolved to default fallback video; aborting to avoid stale/no-op feed run")

    headline, description, cta = generate_post_copy(title)

    final_title = headline.strip() or title.strip()
    if title_exists(feed, final_title):
        suffix = datetime.now(timezone.utc).strftime(" %Y-%m-%d %H%M UTC")
        final_title = (final_title + suffix).strip()
        print(f"Adjusted duplicate headline to unique title: {final_title}")

    description_text = make_description(description, cta)
    slug = create_slug(final_title)
    post_link = generate_video_page(final_title, slug, description_text, video_url, thumb_url)
    new_item = build_item_xml(final_title, description_text, video_url, post_link)

    header, items_blob, footer = split_feed(feed)
    updated_feed = header + new_item + "\n\n" + items_blob.lstrip() + footer
    write_feed(updated_feed)

    print(f"Added new video item at top: {final_title}")


if __name__ == "__main__":
    main()
