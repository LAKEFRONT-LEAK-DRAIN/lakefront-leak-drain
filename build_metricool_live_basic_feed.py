import email.utils
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

SOURCE_FEED = Path("Live_Video_Feed.xml")
OUTPUT_FEED = Path("metricool-live-basic.xml")
MEDIA_NS = "http://search.yahoo.com/mrss/"


def text_of(node: ET.Element | None, fallback: str = "") -> str:
    if node is None or node.text is None:
        return fallback
    value = node.text.strip()
    return value if value else fallback


def pub_date_to_version(pub_date: str) -> str:
    try:
        dt = email.utils.parsedate_to_datetime(pub_date)
        return dt.strftime("%Y%m%d%H%M%S")
    except Exception:
        return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def add_version_param(url: str, version: str) -> str:
    url = re.sub(r"[?&]v=[^&]*", "", (url or "").strip())
    if not url:
        return ""
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}v={version}"


def find_media_thumbnail_url(item: ET.Element) -> str:
    for child in list(item):
        tag = child.tag or ""
        if tag.endswith("thumbnail"):
            url = (child.get("url") or "").strip()
            if url:
                return url
    return ""


def build_basic_feed() -> None:
    ET.register_namespace("media", MEDIA_NS)

    source_tree = ET.parse(SOURCE_FEED)
    source_root = source_tree.getroot()
    source_channel = source_root.find("channel")
    if source_channel is None:
        raise ValueError("Source feed is missing channel element")

    source_items = source_channel.findall("item")
    if not source_items:
        raise ValueError("Source feed has no items")

    source_item = source_items[0]
    item_pub_date = text_of(source_item.find("pubDate"), email.utils.format_datetime(datetime.now(timezone.utc)))

    enclosure = source_item.find("enclosure")
    enclosure_url = enclosure.get("url", "").strip() if enclosure is not None else ""
    enclosure_type = enclosure.get("type", "video/mp4").strip() if enclosure is not None else "video/mp4"
    enclosure_len = enclosure.get("length", "0").strip() if enclosure is not None else "0"
    if not enclosure_url:
        raise ValueError("Top source item is missing enclosure URL")

    version = pub_date_to_version(item_pub_date)
    # Use the HTML page link (not the .mp4 URL) so Metricool doesn't inject
    # a raw video file URL into the post body text.
    page_link = text_of(source_item.find("link"), "")
    item_link = page_link if page_link else add_version_param(enclosure_url, version)
    versioned_enclosure_url = add_version_param(enclosure_url, version)
    thumb_url = find_media_thumbnail_url(source_item) or ""

    # Strict validation: abort if any output URL is empty
    if not item_link:
        raise ValueError("Output item link is empty after versioning")
    if not versioned_enclosure_url:
        raise ValueError("Output enclosure URL is empty after versioning")
    # Use the clean .mp4 URL (no ?v= query param) for enclosure/media:content
    # so Metricool can identify it as a video by the file extension.
    media_url = enclosure_url

    rss = ET.Element("rss", {"version": "2.0", "xmlns:media": MEDIA_NS})
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = text_of(source_channel.find("title"), "Lakefront Live Video Feed")
    ET.SubElement(channel, "link").text = text_of(source_channel.find("link"), "https://lakefrontleakanddrain.com/")
    ET.SubElement(channel, "description").text = text_of(source_channel.find("description"), "Latest live video feed for Metricool.")
    ET.SubElement(channel, "language").text = "en-us"
    ET.SubElement(channel, "lastBuildDate").text = item_pub_date

    out_item = ET.SubElement(channel, "item")
    ET.SubElement(out_item, "title").text = text_of(source_item.find("title"), "Live Video")
    ET.SubElement(out_item, "link").text = item_link
    guid = ET.SubElement(out_item, "guid", {"isPermaLink": "true"})
    guid.text = item_link
    ET.SubElement(out_item, "pubDate").text = item_pub_date
    ET.SubElement(out_item, "description").text = text_of(source_item.find("description"), "Live video update.")
    ET.SubElement(
        out_item,
        "enclosure",
        {"url": media_url, "length": enclosure_len or "0", "type": enclosure_type or "video/mp4"},
    )
    ET.SubElement(
        out_item,
        "media:content",
        {
            "url": media_url,
            "medium": "video",
            "type": enclosure_type or "video/mp4",
            "fileSize": enclosure_len or "0",
        },
    )
    # Omit media:thumbnail in the Metricool feed so video enclosures are
    # prioritized by consumers that otherwise choose image thumbnails.

    ET.indent(rss, space="  ")
    OUTPUT_FEED.write_text(
        ET.tostring(rss, encoding="unicode", xml_declaration=True),
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    build_basic_feed()
