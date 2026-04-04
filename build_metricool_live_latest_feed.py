import email.utils
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

SOURCE_FEED = Path("Live_Video_Feed.xml")
OUTPUT_FEED = Path("metricool-live-latest.xml")


def text_of(node: ET.Element | None, fallback: str = "") -> str:
    if node is None or node.text is None:
        return fallback
    value = node.text.strip()
    return value if value else fallback


def build_latest_feed() -> None:
    source_tree = ET.parse(SOURCE_FEED)
    source_root = source_tree.getroot()
    source_channel = source_root.find("channel")
    if source_channel is None:
        raise ValueError("Source feed is missing channel element")

    first_item = source_channel.find("item")
    if first_item is None:
        raise ValueError("Source feed has no items")

    build_date = text_of(first_item.find("pubDate"), email.utils.format_datetime(datetime.now(timezone.utc)))

    rss = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = text_of(source_channel.find("title"), "Lakefront Live Video Feed")
    ET.SubElement(channel, "link").text = text_of(source_channel.find("link"), "https://lakefrontleakanddrain.com/")
    ET.SubElement(channel, "description").text = text_of(
        source_channel.find("description"), "Latest live video feed for Metricool."
    )
    ET.SubElement(channel, "language").text = "en-us"
    ET.SubElement(channel, "lastBuildDate").text = build_date

    out_item = ET.SubElement(channel, "item")
    item_link = text_of(first_item.find("link"), "https://lakefrontleakanddrain.com/live-video/")

    ET.SubElement(out_item, "title").text = text_of(first_item.find("title"), "Live Video")
    ET.SubElement(out_item, "link").text = item_link
    guid = ET.SubElement(out_item, "guid", {"isPermaLink": "true"})
    guid.text = item_link
    ET.SubElement(out_item, "pubDate").text = text_of(first_item.find("pubDate"), build_date)
    ET.SubElement(out_item, "description").text = text_of(first_item.find("description"), "Live video update.")

    enclosure = first_item.find("enclosure")
    enclosure_url = enclosure.get("url", "").strip() if enclosure is not None else ""
    enclosure_type = enclosure.get("type", "video/mp4").strip() if enclosure is not None else "video/mp4"
    enclosure_len = enclosure.get("length", "1").strip() if enclosure is not None else "1"
    if not enclosure_len or enclosure_len == "0":
        enclosure_len = "1"

    if enclosure_url:
        ET.SubElement(
            out_item,
            "enclosure",
            {"url": enclosure_url, "length": enclosure_len, "type": enclosure_type},
        )

    ET.indent(rss, space="  ")
    OUTPUT_FEED.write_text(
        ET.tostring(rss, encoding="unicode", xml_declaration=True),
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    build_latest_feed()
