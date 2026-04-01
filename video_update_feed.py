import os
import random
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.sax.saxutils import escape

import requests
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

BASE_DIR = Path(__file__).resolve().parent
VIDEO_FEED_PATH = BASE_DIR / "video_feed.xml"
DEFAULT_LINK = "https://lakefrontleakanddrain.com/"
DEFAULT_VIDEO = "https://lakefrontleakanddrain.com/logo-animated.mp4"
MAX_ITEMS = 20
RECENT_TITLE_LOOKBACK = 12
RECENT_VIDEO_LOOKBACK = 12

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
        return True
    tags_lower = (video_tags or "").lower()
    
    bad_keywords = {"car", "auto", "mechanic", "person", "people", "workout", "exercise", "sports", "gym", "music", "dance", "performance"}
    if any(bad in tags_lower for bad in bad_keywords):
        return False
    
    good_keywords = {"plumb", "drain", "sewer", "leak", "pipe", "water", "repair", "fix", "house", "home", "bathroom", "kitchen", "basement"}
    return any(good in tags_lower for good in good_keywords)


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
        
        for vf in v.get("video_files") or []:
            if vf.get("file_type") == "video/mp4" and vf.get("link"):
                candidates.append(vf.get("link"))
    return candidates


def fetch_pixabay_video_candidates(query):
    params = {"q": query, "video_type": "all", "per_page": 15, "safesearch": "true"}
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
        if not is_plumbing_relevant(tags):
            continue
        
        videos_obj = v.get("videos") or {}
        for quality_key in ["medium", "small", "large"]:
            video_data = videos_obj.get(quality_key)
            if video_data and video_data.get("url"):
                candidates.append(video_data.get("url"))
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
    queries = build_video_queries(title, search_keyword)
    recent_video_ids = recent_video_ids or set()

    for query in queries:
        try:
            candidates = fetch_pexels_video_candidates(query)
            if candidates:
                fresh_candidates = [c for c in candidates if canonical_video_id(c) not in recent_video_ids]
                chosen_pool = fresh_candidates if fresh_candidates else candidates
                video_url = random.choice(chosen_pool)
                print(f"Video selected via Pexels using query: {query}")
                if fresh_candidates:
                    print("Selected a fresh (non-recent) video clip")
                else:
                    print("No fresh candidates found for this query; reused an older clip")
                return video_url
        except Exception as e:
            print(f"Pexels search failed for '{query}': {e}")

    print("Pexels exhausted, trying Pixabay fallback...")
    safe_query = normalize_text(search_keyword or "plumbing repair").split()[0:2] 
    safe_query = " ".join(safe_query)
    
    try:
        candidates = fetch_pixabay_video_candidates(safe_query)
        if candidates:
            fresh_candidates = [c for c in candidates if canonical_video_id(c) not in recent_video_ids]
            chosen_pool = fresh_candidates if fresh_candidates else candidates
            video_url = random.choice(chosen_pool)
            print(f"Video selected via Pixabay fallback")
            return video_url
    except Exception as e:
        print(f"Pixabay fallback failed: {e}")

    print("Using default video fallback")
    return video_url


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


def build_item_xml(title, description_text, video_url):
    now = datetime.now(timezone.utc)
    pub_date = now.strftime("%a, %d %b %Y %H:%M:%S GMT")
    guid = f"lakefrontleakanddrain.com/video/{now.strftime('%Y%m%d%H%M%S')}"

    safe_title = escape(title)
    safe_video = escape(video_url)

    return f"""    <item>
      <title>{safe_title}</title>
      <link>{DEFAULT_LINK}</link>
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

    existing_titles = extract_titles(feed)
    title, search_keyword = generate_topic(existing_titles)

    if title_exists(feed, title):
        print(f"Skipped duplicate title: {title}")
        return

    recent_video_ids = extract_recent_video_ids(feed)
    video_url = get_video_url(title, search_keyword, recent_video_ids)
    headline, description, cta = generate_post_copy(title)

    final_title = headline.strip() or title.strip()
    if title_exists(feed, final_title):
        print(f"Skipped duplicate title after headline generation: {final_title}")
        return

    description_text = make_description(description, cta)
    new_item = build_item_xml(final_title, description_text, video_url)

    header, items_blob, footer = split_feed(feed)
    updated_feed = header + new_item + "\n\n" + items_blob.lstrip() + footer
    write_feed(updated_feed)

    print(f"Added new video item at top: {final_title}")


if __name__ == "__main__":
    main()
