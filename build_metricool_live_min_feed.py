import email.utils
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

SOURCE_FEED = Path("Live_Video_Feed.xml")
OUTPUT_FEED = Path("metricool-live-min.xml")


def _text(node: ET.Element | None, default: str = "") -> str:
    if node is None or node.text is None:
        return default
    return node.text.strip()


def _first_item_pubdate(items: list[ET.Element]) -> str:
    for item in items:
        pub_date = _text(item.find("pubDate"))
        if pub_date:
            return pub_date
    return email.utils.format_datetime(datetime.now(timezone.utc))


def build_minimal_feed() -> None:
    source_tree = ET.parse(SOURCE_FEED)
    source_root = source_tree.getroot()
    source_channel = source_root.find("channel")
    if source_channel is None:
        raise ValueError("Source feed is missing channel element")

    source_items = source_channel.findall("item")

    rss = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = _text(
        source_channel.find("title"), "Lakefront Live Video Feed"
    )
    ET.SubElement(channel, "link").text = _text(
        source_channel.find("link"), "https://lakefrontleakanddrain.com/"
    )
    ET.SubElement(channel, "description").text = _text(
        source_channel.find("description"),
        "Minimal live video feed for Metricool.",
    )
    ET.SubElement(channel, "language").text = "en-us"
    ET.SubElement(channel, "lastBuildDate").text = _first_item_pubdate(source_items)

    for item in source_items:
        out_item = ET.SubElement(channel, "item")

        ET.SubElement(out_item, "title").text = _text(item.find("title"), "Live Video")
        ET.SubElement(out_item, "link").text = _text(
            item.find("link"), "https://lakefrontleakanddrain.com/live-video/"
        )

        guid_node = item.find("guid")
        guid = ET.SubElement(
            out_item,
            "guid",
            {
                "isPermaLink": (guid_node.get("isPermaLink") if guid_node is not None else "false")
            },
        )
        guid.text = _text(guid_node, _text(item.find("link"), ""))

        ET.SubElement(out_item, "pubDate").text = _text(item.find("pubDate"), _first_item_pubdate(source_items))
        ET.SubElement(out_item, "description").text = _text(item.find("description"), "Live video update.")

        enclosure_node = item.find("enclosure")
        enclosure_url = ""
        enclosure_length = "0"
        enclosure_type = "video/mp4"
        if enclosure_node is not None:
            enclosure_url = (enclosure_node.get("url") or "").strip()
            enclosure_length = (enclosure_node.get("length") or "0").strip() or "0"
            enclosure_type = (enclosure_node.get("type") or "video/mp4").strip() or "video/mp4"

        if enclosure_url:
            ET.SubElement(
                out_item,
                "enclosure",
                {
                    "url": enclosure_url,
                    "length": enclosure_length,
                    "type": enclosure_type,
                },
            )

    ET.indent(rss, space="  ")
    OUTPUT_FEED.write_text(
        ET.tostring(rss, encoding="unicode", xml_declaration=True),
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    build_minimal_feed()
