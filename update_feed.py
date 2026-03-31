"""import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Tuple
from xml.etree import ElementTree as ET

import requests
from google import genai


# ----------------------------
# Configuration
# ----------------------------
BASE_URL = "https://lakefrontleakanddrain.com/"
DEFAULT_IMAGE_URL = f"{BASE_URL}logo.jpg"
PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"
MODEL_NAME = "gemini-2.5-flash"
FEED_PATH = "feed.xml"


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


dataclass(frozen=True)
class Topic:
    title: str
    search_keyword: str


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise EnvironmentError(f"Required environment variable {name} is not set")
    return value


def get_client() -> genai.Client:
    api_key = _require_env("GEMINI_API_KEY")
    return genai.Client(api_key=api_key)


def generate_topic(client: genai.Client) -> Topic:
    prompt = (
        "Invent a seasonal Cleveland plumbing blog topic. "
        "Output ONLY the Title and a 2-word image search keyword separated by a pipe. "
        "Example: Spring Sump Pump | sump pump"
    )

    resp = client.models.generate_content(model=MODEL_NAME, contents=prompt)
    text = (resp.text or "").strip()

    if not text:
        # Ultra-defensive fallback
        return Topic(title="Seasonal Cleveland Plumbing Tips", search_keyword="plumbing")

    try:
        title, search_keyword = [part.strip() for part in text.split("|", maxsplit=1)]
        if not title:
            raise ValueError("Empty title")
        if not search_keyword:
            search_keyword = "plumbing"
        return Topic(title=title, search_keyword=search_keyword)
    except ValueError:
        return Topic(title=text, search_keyword="plumbing")


def fetch_pexels_image_url(search_keyword: str) -> str:
    """Return a single image URL for the keyword.

    Fallback behavior: if PEXELS_API_KEY is missing or request fails, return DEFAULT_IMAGE_URL.
    """

    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key:
        logger.warning("PEXELS_API_KEY not set; using default logo image.")
        return DEFAULT_IMAGE_URL

    try:
        headers = {"Authorization": api_key}
        params = {"query": search_keyword.strip(), "per_page": 1}
        resp = requests.get(PEXELS_SEARCH_URL, headers=headers, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        photos = data.get("photos") or []
        if not photos:
            logger.warning("No Pexels results for %r; using default logo image.", search_keyword)
            return DEFAULT_IMAGE_URL

        src = (photos[0].get("src") or {})
        url = src.get("large") or src.get("original")
        if not url:
            logger.warning("Pexels response missing src url; using default logo image.")
            return DEFAULT_IMAGE_URL

        return url
    except (requests.RequestException, ValueError, KeyError, IndexError) as e:
        logger.warning("Pexels fetch failed (%s); using default logo image.", e)
        return DEFAULT_IMAGE_URL


def _rfc822_gmt(dt: datetime) -> str:
    # RSS pubDate uses RFC-822 style date in GMT
    return dt.astimezone(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")


def build_rss_item_xml(client: genai.Client, title: str, image_url: str) -> str:
    """Generate an RSS <item> using the model, then normalize/validate via XML parsing.

    - Ensures generated content is well-formed XML
    - Ensures it's actually an <item>
    - Avoids manual '&' double-encoding issues by letting XML serializer escape as needed
    """

    # Keep the model prompt tight, but we still validate output.
    xml_prompt = (
        f"Write a valid RSS <item> block for a post titled '{title}'. "
        f"Use '{BASE_URL}' for link. "
        f"Use {image_url} for enclosure. "
        "Include 2 sentences for Cleveland residents. "
        "Output ONLY raw XML."
    )

    resp = client.models.generate_content(model=MODEL_NAME, contents=xml_prompt)
    raw = (resp.text or "").strip()

    # Strip common Markdown fences
    raw = raw.replace("```xml", "").replace("```", "").strip()

    # Parse and validate
    try:
        elem = ET.fromstring(raw)
    except ET.ParseError as e:
        raise ValueError(f"Model did not return valid XML: {e}") from e

    if elem.tag != "item":
        raise ValueError(f"Expected <item> as root element, got <{elem.tag}>")

    # Ensure there is a pubDate; if missing, add one at 10:00 UTC.
    # (Your previous script used a fixed 10:00:00 GMT time; keep that spirit.)
    if elem.find("pubDate") is None:
        now = datetime.now(timezone.utc)
        normalized = now.replace(hour=10, minute=0, second=0, microsecond=0)
        pub = ET.SubElement(elem, "pubDate")
        pub.text = _rfc822_gmt(normalized)

    # Serialize back to a compact string.
    xml_bytes = ET.tostring(elem, encoding="utf-8", xml_declaration=False)
    return xml_bytes.decode("utf-8")


def insert_item_at_top(feed_path: str, new_item_xml: str) -> None:
    """Insert the item just after <channel> if possible; otherwise before first <item>.

    Falls back to inserting after </description> or </language> if neither is found.
    """

    with open(feed_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_content = []
    inserted = False

    for line in lines:
        new_content.append(line)

        if inserted:
            continue

        if "<channel>" in line:
            new_content.append(f"{new_item_xml}\n\n")
            inserted = True
        elif "<item>" in line:
            # Insert before first item
            new_content.pop()
            new_content.append(f"{new_item_xml}\n\n")
            new_content.append(line)
            inserted = True

    if not inserted:
        for i, line in enumerate(new_content):
            if "</description>" in line or "</language>" in line:
                new_content.insert(i + 1, f"{new_item_xml}\n\n")
                inserted = True
                break

    if not inserted:
        raise RuntimeError("Could not find a suitable insertion point in feed.xml")

    with open(feed_path, "w", encoding="utf-8") as f:
        f.writelines(new_content)


def main() -> None:
    client = get_client()

    topic = generate_topic(client)
    image_url = fetch_pexels_image_url(topic.search_keyword)

    new_item_xml = build_rss_item_xml(client, topic.title, image_url)
    insert_item_at_top(FEED_PATH, new_item_xml)

    logger.info("Verified: %r added to the TOP of the feed.", topic.title)


if __name__ == "__main__":
    main()
"""