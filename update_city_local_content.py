from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus
import xml.etree.ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "city_local_updates.json"
LOCAL_UPDATE_START = "<!-- LOCAL_UPDATE_START -->"
LOCAL_UPDATE_END = "<!-- LOCAL_UPDATE_END -->"
GEOCODE_ENDPOINT = "https://geocoding-api.open-meteo.com/v1/search"
MIN_EVENT_ITEMS = 1
MIN_NEWS_ITEMS = 1
COORD_CACHE: dict[str, tuple[float, float]] = {}


def slug_to_name(slug: str) -> str:
    parts = [p for p in slug.split("-") if p]
    return " ".join(part[:1].upper() + part[1:] for part in parts)


def load_config() -> list[dict[str, Any]]:
    payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    cities = payload.get("cities", [])
    normalized: list[dict[str, Any]] = []

    for city in cities:
        slug = city.get("slug", "").strip()
        name = (city.get("name") or "").strip() or slug_to_name(slug)
        city["name"] = name

        if not city.get("event_query"):
            city["event_query"] = f"{name} OH community events"

        if not city.get("news_query"):
            city["news_query"] = f"{name} OH local news"

        normalized.append(city)

    return normalized


def resolve_coordinates(city: dict[str, Any]) -> tuple[float, float] | None:
    if city.get("lat") is not None and city.get("lon") is not None:
        return float(city["lat"]), float(city["lon"])

    cache_key = city.get("slug") or city.get("name") or city.get("page", "")
    if cache_key in COORD_CACHE:
        return COORD_CACHE[cache_key]

    city_name = city.get("name", "")
    if not city_name:
        return None

    params = {
        "name": city_name,
        "count": 10,
        "language": "en",
        "format": "json",
    }
    response = requests.get(GEOCODE_ENDPOINT, params=params, timeout=20)
    response.raise_for_status()
    results = response.json().get("results", [])

    state = (city.get("state") or "OH").upper()

    for result in results:
        admin1 = (result.get("admin1") or "").strip().lower()
        country = (result.get("country_code") or "").strip().upper()
        if country != "US":
            continue
        if state == "OH" and admin1 != "ohio":
            continue

        coords = (float(result["latitude"]), float(result["longitude"]))
        COORD_CACHE[cache_key] = coords
        return coords

    return None


def normalize_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value or "")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def season_for_month(month: int) -> str:
    if month in (12, 1, 2):
        return "winter"
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    return "fall"


def seasonal_tip(city_name: str, month: int) -> str:
    season = season_for_month(month)
    tips = {
        "winter": f"In {city_name}, freeze-thaw cycles can stress exposed lines. Insulate vulnerable pipes and fix drips early.",
        "spring": f"Spring rain in {city_name} can expose sump and drain issues. Test your sump pump and clear debris from downspout areas.",
        "summer": f"Summer usage spikes can reveal hidden leaks in {city_name}. Keep an eye on pressure changes and unexplained water bill jumps.",
        "fall": f"Before colder weather in {city_name}, check outdoor hose bibs and shutoff valves to reduce freeze damage risk.",
    }
    return tips[season]


def fetch_weather(city: dict[str, Any]) -> dict[str, Any]:
    coords = resolve_coordinates(city)
    if not coords:
        return {}

    endpoint = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": coords[0],
        "longitude": coords[1],
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "timezone": "America/New_York",
        "forecast_days": 5,
    }
    response = requests.get(endpoint, params=params, timeout=20)
    response.raise_for_status()
    data = response.json().get("daily", {})

    if not data or not data.get("time"):
        return {}

    highs = data.get("temperature_2m_max", [])
    lows = data.get("temperature_2m_min", [])
    precip = data.get("precipitation_probability_max", [])

    max_high = round(max(highs)) if highs else None
    min_low = round(min(lows)) if lows else None
    wettest = round(max(precip)) if precip else None

    return {
        "max_high": max_high,
        "min_low": min_low,
        "wettest_precip": wettest,
        "source": "Open-Meteo",
    }


def fetch_rss_items(query: str, limit: int = 3) -> list[dict[str, str]]:
    rss_url = f"https://www.bing.com/news/search?q={quote_plus(query)}&format=rss"
    response = requests.get(rss_url, timeout=20)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    items: list[dict[str, str]] = []

    for item in root.findall("./channel/item"):
        title = normalize_text(item.findtext("title", default=""))
        link = normalize_text(item.findtext("link", default=""))
        pub = normalize_text(item.findtext("pubDate", default=""))
        description = normalize_text(item.findtext("description", default=""))

        if not title or not link:
            continue

        pub_iso = ""
        if pub:
            try:
                pub_iso = parsedate_to_datetime(pub).date().isoformat()
            except Exception:
                pub_iso = ""

        items.append(
            {
                "title": title,
                "link": link,
                "date": pub_iso,
                "description": description,
            }
        )
        if len(items) >= limit:
            break

    return items


def render_link_items(items: list[dict[str, str]], fallback_label: str) -> str:
    if not items:
        return f"<li>No fresh {escape(fallback_label)} items were found in this cycle.</li>"

    lines = []
    for item in items:
        label = escape(item["title"])
        date_suffix = f" ({item['date']})" if item.get("date") else ""
        line = (
            f'<li><a href="{escape(item["link"])}" target="_blank" rel="noopener">'
            f"{label}</a>{escape(date_suffix)}</li>"
        )
        lines.append(line)
    return "".join(lines)


def build_local_update_html(city: dict[str, Any], weather: dict[str, Any], events: list[dict[str, str]], news: list[dict[str, str]]) -> str:
    today = datetime.now(timezone.utc).astimezone().date()
    pretty_date = today.strftime("%B %d, %Y")

    weather_lines = []
    if weather:
        if weather.get("max_high") is not None and weather.get("min_low") is not None:
            weather_lines.append(
                f"<li>5-day temperature range: {weather['min_low']}F to {weather['max_high']}F.</li>"
            )
        if weather.get("wettest_precip") is not None:
            weather_lines.append(
                f"<li>Highest rain chance in next 5 days: {weather['wettest_precip']}%.</li>"
            )

    if not weather_lines:
        weather_lines.append("<li>Weather signal unavailable in this cycle.</li>")

    tip = seasonal_tip(city["name"], today.month)

    return (
        '<div class="card" style="margin-top:16px">'
        f"<h3>Local update for {escape(city['name'])}</h3>"
        f"<p class=\"mini\">Updated {escape(pretty_date)} from public weather and local news/event feeds.</p>"
        '<div class="grid" style="margin-top:10px">'
        '<div class="card"><h3>Weather snapshot</h3><ul class="mini">'
        + "".join(weather_lines)
        + '</ul></div>'
        '<div class="card"><h3>Seasonal plumbing tip</h3>'
        f'<p class="mini">{escape(tip)}</p>'
        '</div>'
        '</div>'
        '<div class="grid" style="margin-top:10px">'
        '<div class="card"><h3>Community events and notices</h3><ul class="mini">'
        + render_link_items(events, "community event")
        + '</ul></div>'
        '<div class="card"><h3>Top local news stories</h3><ul class="mini">'
        + render_link_items(news, "local news")
        + '</ul></div>'
        '</div>'
        '<p class="mini" style="margin-top:10px">Sources: Open-Meteo and Bing News RSS. Links open external sites.</p>'
        '</div>'
    )


def quality_passes(weather: dict[str, Any], events: list[dict[str, str]], news: list[dict[str, str]]) -> tuple[bool, str]:
    has_weather = bool(weather) and (
        weather.get("max_high") is not None
        or weather.get("min_low") is not None
        or weather.get("wettest_precip") is not None
    )

    if not has_weather:
        return False, "missing weather signal"

    if len(events) < MIN_EVENT_ITEMS:
        return False, f"insufficient event items ({len(events)})"

    if len(news) < MIN_NEWS_ITEMS:
        return False, f"insufficient news items ({len(news)})"

    return True, "ok"


def upsert_local_update(page_path: Path, content: str) -> bool:
    if not page_path.exists():
        raise FileNotFoundError(f"Missing city page: {page_path}")

    html = page_path.read_text(encoding="utf-8")
    wrapped = f"{LOCAL_UPDATE_START}\n{content}\n{LOCAL_UPDATE_END}"

    pattern = re.compile(
        rf"{re.escape(LOCAL_UPDATE_START)}.*?{re.escape(LOCAL_UPDATE_END)}",
        flags=re.DOTALL,
    )

    if pattern.search(html):
        updated = pattern.sub(wrapped, html, count=1)
    else:
        marker = "\n<section style=\"background:var(--bg)\">"
        if marker in html:
            updated = html.replace(marker, "\n" + wrapped + marker, 1)
        else:
            updated = html + "\n" + wrapped + "\n"

    if updated == html:
        return False

    page_path.write_text(updated, encoding="utf-8")
    return True


def main() -> None:
    cities = load_config()
    changed_pages = 0
    skipped_pages = 0

    for city in cities:
        weather = {}
        events: list[dict[str, str]] = []
        news: list[dict[str, str]] = []

        try:
            weather = fetch_weather(city)
        except Exception as exc:
            print(f"[{city['name']}] weather fetch failed: {exc}")

        try:
            events = fetch_rss_items(city["event_query"], limit=3)
        except Exception as exc:
            print(f"[{city['name']}] event feed fetch failed: {exc}")

        try:
            news = fetch_rss_items(city["news_query"], limit=3)
        except Exception as exc:
            print(f"[{city['name']}] news feed fetch failed: {exc}")

        ok, reason = quality_passes(weather, events, news)
        if not ok:
            skipped_pages += 1
            print(f"Skipped local section: {city['page']} ({reason})")
            continue

        block = build_local_update_html(city, weather, events, news)
        page = ROOT / city["page"]
        changed = upsert_local_update(page, block)
        if changed:
            changed_pages += 1
            print(f"Updated local section: {city['page']}")
        else:
            print(f"No content change: {city['page']}")

    print(
        "Done. "
        f"City pages refreshed: {changed_pages}/{len(cities)}. "
        f"Skipped for quality: {skipped_pages}."
    )


if __name__ == "__main__":
    main()
