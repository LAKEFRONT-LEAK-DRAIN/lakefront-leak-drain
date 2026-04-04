import re
import shutil
import subprocess
import sys
from pathlib import Path

MAX_FILE_BYTES = 20 * 1024 * 1024  # 20 MB hard ceiling for Metricool

BASE_DIR = Path(__file__).resolve().parent
SOURCE_FEED = BASE_DIR / "Live_Video_Feed.xml"
VIDEO_DIR = BASE_DIR / "live-video"
GENERATED_DIR = VIDEO_DIR / "generated"
GENERATED_URL_PREFIX = "https://lakefrontleakanddrain.com/live-video/generated/"
MAX_FILES = 3


def extract_top_generated_filenames(feed_text: str, limit: int) -> list[str]:
    item_blocks = re.findall(r"<item>.*?</item>", feed_text, flags=re.S)
    names: list[str] = []
    seen = set()
    for item in item_blocks:
        m = re.search(r"<enclosure\b[^>]*\burl=\"([^\"]+)\"", item, flags=re.I)
        if not m:
            continue
        url = m.group(1).strip()
        if not url.startswith(GENERATED_URL_PREFIX):
            continue
        filename = url.split("/")[-1]
        if not filename or filename in seen:
            continue
        seen.add(filename)
        names.append(filename)
        if len(names) >= limit:
            break
    return names


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _run_ffmpeg_encode(src_path: Path, tmp_path: Path, video_bitrate_k: int) -> bool:
    """Run ffmpeg encode at the specified video bitrate (in kbps)."""
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src_path),
        "-c:v",
        "libx264",
        "-b:v",
        f"{video_bitrate_k}k",
        "-maxrate",
        f"{int(video_bitrate_k * 1.25)}k",
        "-bufsize",
        f"{video_bitrate_k * 2}k",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-ar",
        "44100",
        "-ac",
        "2",
        str(tmp_path),
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        print(f"ffmpeg failed at {video_bitrate_k}k for {src_path.name}: {e.stderr.decode(errors='ignore')[:400]}")
        return False


def normalize_video(src_path: Path) -> bool:
    tmp_path = src_path.with_suffix(".tmp.mp4")
    # First pass: target 4 000 kbps — keeps an 8-second 720p clip well under 15 MB.
    primary_bitrate = 4000
    if not _run_ffmpeg_encode(src_path, tmp_path, primary_bitrate):
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        return False

    # If the first pass still exceeds the 20 MB ceiling, re-encode at 2 000 kbps.
    if tmp_path.stat().st_size > MAX_FILE_BYTES:
        print(f"{src_path.name}: first-pass output is {tmp_path.stat().st_size // (1024*1024)} MB, re-encoding at 2000k.")
        fallback_tmp = src_path.with_suffix(".tmp2.mp4")
        ok = _run_ffmpeg_encode(tmp_path, fallback_tmp, 2000)
        tmp_path.unlink(missing_ok=True)
        if not ok:
            if fallback_tmp.exists():
                fallback_tmp.unlink(missing_ok=True)
            return False
        fallback_tmp.rename(tmp_path)

    tmp_path.replace(src_path)
    size_mb = src_path.stat().st_size / (1024 * 1024)
    print(f"{src_path.name}: final size {size_mb:.1f} MB")
    return True


def main() -> int:
    if not SOURCE_FEED.exists():
        print("Live_Video_Feed.xml not found. Skipping optimization.")
        return 0

    if not GENERATED_DIR.exists():
        print("No generated video directory found. Skipping optimization.")
        return 0

    if not ffmpeg_available():
        print("ffmpeg not available in runner. Skipping optimization.")
        return 0

    feed_text = SOURCE_FEED.read_text(encoding="utf-8", errors="ignore")
    targets = extract_top_generated_filenames(feed_text, MAX_FILES)
    if not targets:
        print("No generated videos in top feed items. Nothing to optimize.")
        return 0

    optimized = 0
    for name in targets:
        path = GENERATED_DIR / name
        if not path.exists():
            print(f"Missing generated asset: {name}")
            continue
        print(f"Optimizing {name}...")
        if normalize_video(path):
            optimized += 1

    print(f"Optimization complete. Optimized {optimized}/{len(targets)} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
