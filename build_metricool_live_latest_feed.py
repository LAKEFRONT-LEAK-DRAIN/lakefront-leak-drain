import email.utils
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import requests

SOURCE_FEED = Path("Live_Video_Feed.xml")
OUTPUT_FEED = Path("metricool-live-latest.xml")
MAX_ITEMS = 3


def text_of(node: ET.Element | None, fallback: str = "") -> str:
    if node is None or node.text is None:
        return fallback
    value = node.text.strip()
    return value if value else fallback


def pub_date_to_version(pub_date: str) -> str:
    """Convert an RFC 2822 pubDate string to a compact YYYYMMDDHHMMSS version token.

    Falls back to the current UTC time if parsing fails.  The token is used as
    a ``?v=`` query-string suffix on video URLs to bust Metricool's cache when
    the video file is replaced but the filename stays the same.
    """
    try:
        dt = email.utils.parsedate_to_datetime(pub_date)
        return dt.strftime("%Y%m%d%H%M%S")
    except Exception:
        return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def add_version_param(url: str, version: str) -> str:
    """Append ``?v=<version>`` to *url*, replacing any existing ``v=`` param."""
    url = re.sub(r"[?&]v=[^&]*", "", url)
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}v={version}"


def resolve_enclosure_length(declared_len: str, url: str) -> str:
    """Return a best-effort byte length string for an enclosure.

    If the declared length is missing, zero, or the placeholder '1', attempt an
    HTTP HEAD request to get the real Content-Length.  Falls back to '0' on
    failure so the feed remains valid without a misleading size.
    """
    clean = (declared_len or "").strip()
    if clean and clean not in ("0", "1"):
        return clean

    if not url:
        return "0"

    try:
        resp = requests.head(url.split("?")[0], allow_redirects=True, timeout=8,
                             headers={"User-Agent": "LakefrontFeedBuilder/1.0"})
        content_length = resp.headers.get("Content-Length", "").strip()
        if content_length.isdigit() and int(content_length) > 1:
            return content_length
    except Exception:
        pass

    return "0"


def build_latest_feed() -> None:
    source_tree = ET.parse(SOURCE_FEED)
    source_root = source_tree.getroot()
    source_channel = source_root.find("channel")
    if source_channel is None:
        raise ValueError("Source feed is missing channel element")

    source_items = source_channel.findall("item")
    if not source_items:
        raise ValueError("Source feed has no items")

    build_date = text_of(source_items[0].find("pubDate"), email.utils.format_datetime(datetime.now(timezone.utc)))

    rss = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = text_of(source_channel.find("title"), "Lakefront Live Video Feed")
    ET.SubElement(channel, "link").text = text_of(source_channel.find("link"), "https://lakefrontleakanddrain.com/")
    ET.SubElement(channel, "description").text = text_of(
        source_channel.find("description"), "Latest live video feed for Metricool."
    )
    ET.SubElement(channel, "language").text = "en-us"
    ET.SubElement(channel, "lastBuildDate").text = build_date

    for source_item in source_items[:MAX_ITEMS]:
        out_item = ET.SubElement(channel, "item")
        page_link = text_of(source_item.find("link"), "https://lakefrontleakanddrain.com/live-video/")

        enclosure = source_item.find("enclosure")
        enclosure_url = enclosure.get("url", "").strip() if enclosure is not None else ""
        enclosure_type = enclosure.get("type", "video/mp4").strip() if enclosure is not None else "video/mp4"
        enclosure_len = enclosure.get("length", "0").strip() if enclosure is not None else "0"

        enclosure_len = resolve_enclosure_length(enclosure_len, enclosure_url)

        # Derive a version token from the item's pubDate for cache-busting.
        item_pub_date = text_of(source_item.find("pubDate"), build_date)
        version = pub_date_to_version(item_pub_date)

        # Prefer direct MP4 as link/guid to maximise chance of true video ingestion.
        # Append ?v=<version> so Metricool re-downloads when the file is replaced.
        raw_item_link = enclosure_url or page_link
        item_link = add_version_param(raw_item_link, version)
        versioned_enclosure_url = add_version_param(enclosure_url, version) if enclosure_url else ""

        ET.SubElement(out_item, "title").text = text_of(source_item.find("title"), "Live Video")
        ET.SubElement(out_item, "link").text = item_link
        guid = ET.SubElement(out_item, "guid", {"isPermaLink": "true"})
        guid.text = item_link
        ET.SubElement(out_item, "pubDate").text = item_pub_date
        base_desc = text_of(source_item.find("description"), "Live video update.")
        ET.SubElement(out_item, "description").text = f"{base_desc} Watch page: {page_link}"

        if versioned_enclosure_url:
            ET.SubElement(
                out_item,
                "enclosure",
                {"url": versioned_enclosure_url, "length": enclosure_len, "type": enclosure_type},
            )

    ET.indent(rss, space="  ")
    OUTPUT_FEED.write_text(
        ET.tostring(rss, encoding="unicode", xml_declaration=True),
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    build_latest_feed()
