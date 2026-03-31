import os
import re
import requests
from google import genai
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from xml.sax.saxutils import escape

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

FEED_PATH = "feed.xml"
DEFAULT_LINK = "https://lakefrontleakanddrain.com/"
DEFAULT_IMAGE = "https://lakefrontleakanddrain.com/logo.jpg"
DEFAULT_VIDEO = "https://lakefrontleakanddrain.com/logo-animated.mp4"
MAX_ITEMS = 75
RECENT_TITLE_LOOKBACK = 12


def generate_topic(existing_titles):
    recent_titles_text = "\n".join(f"- {t}" for t in existing_titles[:RECENT_TITLE_LOOKBACK]) or "- None"

    prompt = f"""
Invent ONE strong local SEO plumbing topic for Lakefront Leak & Drain in Cleveland, Ohio.

Avoid repeating or closely mimicking these recent titles:
{recent_titles_text}

Rules:
- Make it specific to homeowners, property managers, drains, sewer lines, leaks, sump pumps, water heaters, inspections, backups, or plumbing emergencies.
- Favor seasonal relevance for Cleveland.
- Output ONLY this format:
Title | image keyword
- The image keyword should be 2 to 4 words.
""".strip()

    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    text = (resp.text or "").strip()

    try:
        title, search_keyword = [x.strip() for x in text.split("|", 1)]
    except Exception:
        title = text or "Cleveland Plumbing Tips for Homeowners"
        search_keyword = "plumbing service"

    return title, search_keyword


def get_image_url(search_keyword):
    image_url = DEFAULT_IMAGE
    try:
        headers = {"Authorization": os.environ["PEXELS_API_KEY"]}
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": search_keyword.strip(), "per_page": 1, "orientation": "landscape"},
            headers=headers,
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        photos = data.get("photos") or []
        if photos:
            image_url = photos[0]["src"]["large"]
    except Exception:
        pass
    return image_url


def generate_post_copy(title):
    prompt = f"""
Write RSS-ready marketing copy for this title:
{title}

Return ONLY valid JSON with keys:
headline
description
cta

Rules:
- Audience: Cleveland homeowners and property managers.
- Tone: helpful, local, trustworthy, urgent but not spammy.
- description must be exactly 2 sentences.
- cta must be short.
- No markdown.
""".strip()

    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    text = (resp.text or "").strip()

    # tolerant fallback parser without importing json if model wraps text poorly
    import json
    try:
        data = json.loads(text)
        headline = (data.get("headline") or title).strip()
        description = (data.get("description") or "").strip()
        cta = (data.get("cta") or "Call Lakefront Leak & Drain today.").strip()
    except Exception:
        headline = title
        description = (
            f"Cleveland homeowners and property managers can avoid expensive plumbing damage by acting early when warning signs appear. "
            f"Lakefront Leak & Drain helps diagnose issues quickly and fix them before they become emergencies."
        )
        cta = "Call Lakefront Leak & Drain today."

    if not description:
        description = (
            f"Cleveland homeowners and property managers can avoid expensive plumbing damage by acting early when warning signs appear. "
            f"Lakefront Leak & Drain helps diagnose issues quickly and fix them before they become emergencies."
        )

    return headline, description, cta


def make_description(description, cta):
    return f"{description} {cta}".strip()


def build_item_xml(title, description_text, image_url):
    now = datetime.now(timezone.utc)
    pub_date = now.strftime("%a, %d %b %Y %H:%M:%S GMT")
    guid = f"lakefrontleakanddrain.com/post/{now.strftime('%Y%m%d%H%M%S')}"

    return f"""    <item>
      <title>{escape(title)}</title>
      <link>{DEFAULT_LINK}</link>
      <guid isPermaLink="false">{guid}</guid>
      <pubDate>{pub_date}</pubDate>
      <description><![CDATA[{description_text}]]></description>
      <media:content url="{escape(DEFAULT_VIDEO)}" medium="video" />
      <enclosure url="{escape(image_url)}" length="0" type="image/jpeg" />
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
    normalized = title.strip().lower()
    return normalized in existing_titles


def split_feed(feed_text):
    first_item_match = re.search(r"<item>", feed_text)
    end_match = re.search(r"</channel>\s*</rss>\s*$", feed_text, flags=re.S)

    if not end_match:
        raise ValueError("Could not find </channel></rss> in feed.xml")

    if first_item_match:
        header = feed_text[:first_item_match.start()]
        items_blob = feed_text[first_item_match.start():end_match.start()]
    else:
        channel_close = feed_text.rfind("</channel>")
        if channel_close == -1:
            raise ValueError("Could not find </channel> in feed.xml")
        header = feed_text[:channel_close]
        items_blob = ""

    footer = feed_text[end_match.start():]
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

    # Deduplicate by exact title, keeping newest if possible.
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

    with open(FEED_PATH, "w", encoding="utf-8") as f:
        f.write(final_text)


def main():
    with open(FEED_PATH, "r", encoding="utf-8") as f:
        feed = f.read()

    existing_titles = extract_titles(feed)
    title, search_keyword = generate_topic(existing_titles)

    if title_exists(feed, title):
        print(f"Skipped duplicate title: {title}")
        return

    image_url = get_image_url(search_keyword)
    headline, description, cta = generate_post_copy(title)

    # Use model-improved headline, but avoid duplicates again just in case.
    final_title = headline.strip() or title.strip()
    if title_exists(feed, final_title):
        print(f"Skipped duplicate title after headline generation: {final_title}")
        return

    description_text = make_description(description, cta)
    new_item = build_item_xml(final_title, description_text, image_url)

    header, items_blob, footer = split_feed(feed)
    updated_feed = header + new_item + "\n\n" + items_blob.lstrip() + footer
    write_feed(updated_feed)

    print(f"Added new item at top: {final_title}")


if __name__ == "__main__":
    main()
