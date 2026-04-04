import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import parse_qs, urlparse

FEED_PATH = Path("metricool-live-basic.xml")
MAX_ITEM_SIZE_BYTES = 20 * 1024 * 1024
REQUIRED_ITEM_COUNT = 3
SITE_PREFIX = "https://lakefrontleakanddrain.com/"


def local_path_from_url(url: str) -> Path | None:
    parsed = urlparse(url)
    if not url.startswith(SITE_PREFIX):
        return None
    relative = parsed.path.lstrip("/")
    if not relative:
        return None
    return Path(relative)


def has_version_param(url: str) -> bool:
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    value = params.get("v", [""])[0].strip()
    return bool(value and value.isdigit())


def fail(msg: str) -> None:
    print(f"VALIDATION FAILED: {msg}")
    raise SystemExit(1)


def main() -> int:
    if not FEED_PATH.exists():
        fail(f"Missing feed file: {FEED_PATH}")

    tree = ET.parse(FEED_PATH)
    root = tree.getroot()
    channel = root.find("channel")
    if channel is None:
        fail("Feed has no <channel> element")

    items = channel.findall("item")
    if len(items) != REQUIRED_ITEM_COUNT:
        fail(f"Expected exactly {REQUIRED_ITEM_COUNT} items, found {len(items)}")

    for idx, item in enumerate(items, start=1):
        link = (item.findtext("link") or "").strip()
        guid = (item.findtext("guid") or "").strip()
        enclosure = item.find("enclosure")

        if not enclosure:
            fail(f"Item {idx} is missing <enclosure>")

        enclosure_url = (enclosure.get("url") or "").strip()
        enclosure_type = (enclosure.get("type") or "").strip().lower()

        if not enclosure_url:
            fail(f"Item {idx} enclosure is missing URL")
        if enclosure_type != "video/mp4":
            fail(f"Item {idx} enclosure type must be video/mp4, got: {enclosure_type}")

        for field_name, value in (("link", link), ("guid", guid), ("enclosure", enclosure_url)):
            if not value:
                fail(f"Item {idx} has empty {field_name}")
            if ".mp4" not in value.lower():
                fail(f"Item {idx} {field_name} is not an MP4 URL: {value}")
            if not has_version_param(value):
                fail(f"Item {idx} {field_name} is missing numeric ?v= cache-buster: {value}")

        local_video_path = local_path_from_url(enclosure_url)
        if local_video_path is not None:
            if not local_video_path.exists():
                fail(f"Item {idx} local MP4 missing: {local_video_path}")
            size_bytes = local_video_path.stat().st_size
            if size_bytes > MAX_ITEM_SIZE_BYTES:
                mb = size_bytes / (1024 * 1024)
                fail(
                    f"Item {idx} MP4 exceeds 20 MB ({mb:.1f} MB): {local_video_path}"
                )

    print(f"Validation passed for {len(items)} items in {FEED_PATH}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
