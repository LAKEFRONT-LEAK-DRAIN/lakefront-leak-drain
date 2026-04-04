"""Patch /blog/*.html pages to include Open Graph video meta tags.

When Metricool (or any social crawler) visits a blog post URL, it checks
Open Graph meta tags for embeddable video. Blog posts need og:type=video.other
and the og:video tag family so that video previews appear rather than plain
image cards.

This script:
  1. Reads the latest video URL/title from Live_Video_Feed.xml.
  2. Scans every *.html file inside /blog/ (non-recursively at top level).
  3. For files that already have a full og:video tag, it leaves them alone.
  4. For files that are missing og:video tags, it injects the full video tag
     block immediately after the existing og:image tag (or og:url if no image).
"""

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from html import escape as html_escape

BASE_DIR = Path(__file__).resolve().parent
BLOG_DIR = BASE_DIR / "blog"
SOURCE_FEED = BASE_DIR / "Live_Video_Feed.xml"

# Canonical dimensions of generated 9:16 720p videos.
VIDEO_WIDTH = "720"
VIDEO_HEIGHT = "1280"


def get_latest_video_info() -> tuple[str, str]:
    """Return (enclosure_url, title) for the most recent item in Live_Video_Feed.xml."""
    if not SOURCE_FEED.exists():
        return ("", "")
    try:
        tree = ET.parse(SOURCE_FEED)
    except ET.ParseError:
        return ("", "")
    root = tree.getroot()
    channel = root.find("channel")
    if channel is None:
        return ("", "")
    # Handle namespace-prefixed enclosure tags from WordPress feeds.
    first_item = channel.find("item")
    if first_item is None:
        return ("", "")
    title = (first_item.findtext("title") or "").strip()
    enclosure = first_item.find("enclosure")
    if enclosure is None:
        return ("", title)
    url = enclosure.get("url", "").strip()
    return (url, title)


OG_VIDEO_BLOCK_TEMPLATE = """\
    <meta property="og:type" content="video.other">
    <meta property="og:video" content="{url}">
    <meta property="og:video:secure_url" content="{url}">
    <meta property="og:video:type" content="video/mp4">
    <meta property="og:video:width" content="{width}">
    <meta property="og:video:height" content="{height}">"""


def build_og_video_block(url: str) -> str:
    safe_url = html_escape(url)
    return OG_VIDEO_BLOCK_TEMPLATE.format(url=safe_url, width=VIDEO_WIDTH, height=VIDEO_HEIGHT)


# Regex that matches an og:video tag already present in the file.
_RE_ALREADY_HAS_VIDEO = re.compile(
    r'<meta\s[^>]*property=["\']og:video["\']', re.IGNORECASE
)

# We inject the video block after og:image (or og:url as fallback).
_RE_INJECT_ANCHOR = re.compile(
    r'(<meta\s[^>]*property=["\']og:(?:image|url)["\'][^>]*>)',
    re.IGNORECASE,
)

# Replace og:type=article with og:type=video.other so scrapers treat it as video.
_RE_OG_TYPE_ARTICLE = re.compile(
    r'(<meta\s[^>]*property=["\']og:type["\']\s[^>]*content=["\'])article(["\'])',
    re.IGNORECASE,
)


def patch_html(html: str, video_url: str) -> tuple[str, bool]:
    """Return (patched_html, was_changed)."""
    if _RE_ALREADY_HAS_VIDEO.search(html):
        return html, False

    block = build_og_video_block(video_url)

    # Find the LAST og:image or og:url tag and inject after it.
    anchors = list(_RE_INJECT_ANCHOR.finditer(html))
    if not anchors:
        # No suitable anchor — inject before </head>.
        if "</head>" in html:
            patched = html.replace("</head>", block + "\n</head>", 1)
        else:
            return html, False
    else:
        anchor = anchors[-1]
        insert_pos = anchor.end()
        patched = html[:insert_pos] + "\n" + block + html[insert_pos:]

    # Upgrade og:type from article → video.other.
    patched = _RE_OG_TYPE_ARTICLE.sub(r"\1video.other\2", patched)
    return patched, True


def main() -> int:
    video_url, video_title = get_latest_video_info()
    if not video_url:
        print("No enclosure URL found in Live_Video_Feed.xml — nothing to patch.")
        return 0

    print(f"Patching blog pages with video URL: {video_url}")
    print(f"Video title: {video_title}")

    html_files = sorted(BLOG_DIR.glob("*.html"))
    if not html_files:
        print("No *.html files found in blog/. Skipping.")
        return 0

    patched_count = 0
    skipped_count = 0
    for html_path in html_files:
        original = html_path.read_text(encoding="utf-8", errors="replace")
        patched, changed = patch_html(original, video_url)
        if changed:
            html_path.write_text(patched, encoding="utf-8", newline="\n")
            print(f"  Patched: {html_path.name}")
            patched_count += 1
        else:
            skipped_count += 1

    print(f"Done. Patched {patched_count} pages, skipped {skipped_count} (already had og:video).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
