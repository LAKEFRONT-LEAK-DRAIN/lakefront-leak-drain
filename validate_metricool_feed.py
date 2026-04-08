import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests

FEED_PATH = Path("metricool-live-basic.xml")
MAX_ITEM_SIZE_BYTES = 20 * 1024 * 1024
MIN_ITEM_COUNT = 1
MAX_ITEM_COUNT = 3
SITE_PREFIX = "https://lakefrontleakanddrain.com/"
SITE_HOSTS = {"lakefrontleakanddrain.com", "www.lakefrontleakanddrain.com"}
REQUEST_TIMEOUT_SECONDS = 12
USER_AGENT = "LakefrontMetricoolValidator/1.0"
VALIDATE_REMOTE_LOCAL_SITE_ASSETS = os.environ.get(
    "VALIDATE_REMOTE_LOCAL_SITE_ASSETS", "false"
).strip().lower() in {"1", "true", "yes", "on"}


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


def normalized_video_path(url: str) -> str:
    parsed = urlparse(url)
    return parsed.path.strip().lower()


def is_site_url(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.netloc or "").strip().lower()
    return host in SITE_HOSTS


def ensure_remote_video_headers(item_idx: int, url: str) -> None:
    try:
        response = requests.head(
            url,
            allow_redirects=True,
            timeout=REQUEST_TIMEOUT_SECONDS,
            headers={"User-Agent": USER_AGENT},
        )
    except Exception as e:
        fail(f"Item {item_idx} remote HEAD failed for enclosure URL {url}: {e}")

    if response.status_code >= 400:
        fail(f"Item {item_idx} enclosure URL returned HTTP {response.status_code}: {url}")

    content_type = (response.headers.get("Content-Type") or "").strip().lower()
    if "video/mp4" not in content_type:
        fail(f"Item {item_idx} enclosure Content-Type is not video/mp4: {content_type or '[missing]'}")

    # Enforce strict CORS/range requirements only for first-party assets.
    # External CDNs (e.g., Pixabay) are allowed as long as they return valid MP4s.
    final_url = (response.url or "").strip()
    if not is_site_url(url) and not is_site_url(final_url):
        return

    cors = (response.headers.get("Access-Control-Allow-Origin") or "").strip()
    if cors != "*":
        fail(f"Item {item_idx} enclosure missing wildcard CORS header: {url}")

    accept_ranges = (response.headers.get("Accept-Ranges") or "").strip().lower()
    if "bytes" not in accept_ranges:
        fail(f"Item {item_idx} enclosure missing Accept-Ranges: bytes: {url}")


def should_validate_remote_headers(local_video_path: Path | None) -> bool:
    if local_video_path is None:
        return True
    return VALIDATE_REMOTE_LOCAL_SITE_ASSETS


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
    if len(items) < MIN_ITEM_COUNT or len(items) > MAX_ITEM_COUNT:
        fail(f"Expected {MIN_ITEM_COUNT} to {MAX_ITEM_COUNT} items, found {len(items)}")

    for idx, item in enumerate(items, start=1):
        link = (item.findtext("link") or "").strip()
        guid = (item.findtext("guid") or "").strip()
        enclosure = item.find("enclosure")

        # ElementTree elements are falsey when they have no children, so use
        # explicit None check for self-closing <enclosure ... /> tags.
        if enclosure is None:
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
            if any(ch.isspace() for ch in value):
                fail(f"Item {idx} {field_name} URL contains whitespace: {value}")

            parsed = urlparse(value)
            if parsed.scheme.lower() != "https" or not parsed.netloc:
                fail(f"Item {idx} {field_name} must be an absolute HTTPS URL: {value}")

        # Metricool feed format may use either:
        # - HTML page link/guid + MP4 enclosure, or
        # - direct MP4 link/guid + MP4 enclosure.
        link_is_mp4 = ".mp4" in link.lower()
        guid_is_mp4 = ".mp4" in guid.lower()
        if link_is_mp4 != guid_is_mp4:
            fail(
                f"Item {idx} link/guid media style mismatch: link={link}, guid={guid}"
            )

        if ".mp4" not in enclosure_url.lower():
            fail(f"Item {idx} enclosure is not an MP4 URL: {enclosure_url}")

        link_path = normalized_video_path(link)
        guid_path = normalized_video_path(guid)
        if link_path != guid_path:
            fail(
                f"Item {idx} link/guid paths differ: link={link_path}, guid={guid_path}"
            )

        local_video_path = local_path_from_url(enclosure_url)
        if local_video_path is not None:
            if not local_video_path.exists():
                fail(f"Item {idx} local MP4 missing: {local_video_path}")
            size_bytes = local_video_path.stat().st_size
            if size_bytes <= 0:
                fail(f"Item {idx} local MP4 is empty: {local_video_path}")
            if size_bytes > MAX_ITEM_SIZE_BYTES:
                mb = size_bytes / (1024 * 1024)
                fail(
                    f"Item {idx} MP4 exceeds 20 MB ({mb:.1f} MB): {local_video_path}"
                )

        if should_validate_remote_headers(local_video_path):
            ensure_remote_video_headers(idx, enclosure_url)
        else:
            print(
                f"Item {idx}: skipping remote header check for local site asset before deploy: {enclosure_url}"
            )

    print(f"Validation passed for {len(items)} items in {FEED_PATH}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
