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

BASE_DIR = Path(__file__).resolve().parent
SITE_BASE_URL = "https://lakefrontleakanddrain.com"
VIDEO_FEED_PATH = BASE_DIR / "video_feed.xml"
DEFAULT_LINK = "https://lakefrontleakanddrain.com/"
DEFAULT_VIDEO = "https://lakefrontleakanddrain.com/logo-animated.mp4"
MAX_ITEMS = 20
RECENT_TITLE_LOOKBACK = 12
RECENT_VIDEO_LOOKBACK = 12
ALLOW_PEXELS_FALLBACK = os.environ.get("ALLOW_PEXELS_FALLBACK", "false").strip().lower() == "true"

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


def generate_topic(existing_titles):
    recent_titles_text = "\n".join(f"- {t}" for t in existing_titles[:RECENT_TITLE_LOOKBACK]) or "- None"

    prompt = f"""
Invent ONE strong short-form VIDEO topic for Lakefront Leak & Drain in Cleveland, Ohio.

Avoid repeating or closely mimicking these recent titles:
{recent_titles_text}

Rules:
- Make it specific to homeowners, drains, sewer lines, leaks, sump pumps, frozen pipes, water heaters, inspections, backups, or plumbing emergencies.
- Favor seasonal relevance for Cleveland.
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

        thumb_url = (v.get("image") or "").strip()
        
        for vf in v.get("video_files") or []:
            if vf.get("file_type") == "video/mp4" and vf.get("link"):
                candidates.append(
                    {
                        "video_url": vf.get("link"),
                        "thumb_url": thumb_url,
                        "id": f"pexels:{video_id}" if video_id else "",
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

        # Pixabay tags can be sparse. For primary-source mode, allow neutral tags
        # and rely on bad-keyword rejection plus query quality.
        videos_obj = v.get("videos") or {}
        for quality_key in ["medium", "small", "large"]:
            video_data = videos_obj.get(quality_key)
            if video_data and video_data.get("url"):
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
    return video_url, thumb_url


def generate_video_page(title, slug, description_text, video_url, thumb_url):
    video_dir = BASE_DIR / "video"
    if not video_dir.exists():
        video_dir.mkdir(parents=True, exist_ok=True)

    page_url = f"{SITE_BASE_URL}/video/{slug}.html"
    safe_title = html_escape(title)
    safe_desc = html_escape(description_text)
    safe_video = html_escape(video_url)
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


def build_item_xml(title, description_text, video_url, post_link):
    now = datetime.now(timezone.utc)
    pub_date = now.strftime("%a, %d %b %Y %H:%M:%S GMT")
    guid = f"lakefrontleakanddrain.com/video/{now.strftime('%Y%m%d%H%M%S')}"

    safe_title = escape(title)
    safe_video = escape(video_url)

    return f"""    <item>
      <title>{safe_title}</title>
            <link>{post_link}</link>
      <guid isPermaLink=\"false\">{guid}</guid>
      <pubDate>{pub_date}</pubDate>
      <description><![CDATA[{description_text}]]></description>
      <enclosure url=\"{safe_video}\" length=\"0\" type=\"video/mp4\" />
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
    title, search_keyword = generate_topic(existing_titles)

    if title_exists(feed, title):
        print(f"Skipped duplicate title: {title}")
        return

    recent_video_ids = extract_recent_video_ids(feed)
    video_url, thumb_url = get_video_url(title, search_keyword, recent_video_ids)
    headline, description, cta = generate_post_copy(title)

    final_title = headline.strip() or title.strip()
    if title_exists(feed, final_title):
        print(f"Skipped duplicate title after headline generation: {final_title}")
        return

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
