import os
import requests
from google import genai
from datetime import datetime
from xml.sax.saxutils import escape

client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])

FEED_PATH = 'feed.xml'
DEFAULT_LINK = 'https://lakefrontleakanddrain.com/'
DEFAULT_IMAGE = 'https://lakefrontleakanddrain.com/logo.jpg'


def generate_topic():
    prompt = (
        "Invent a seasonal Cleveland plumbing blog topic. "
        "Output ONLY the Title and a 2-word image search keyword separated by a pipe. "
        "Example: Spring Sump Pump | sump pump"
    )
    resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    text = resp.text.strip()

    try:
        title, search_keyword = [x.strip() for x in text.split('|', 1)]
    except Exception:
        title = text
        search_keyword = "plumbing"

    return title, search_keyword


def get_image_url(search_keyword):
    image_url = DEFAULT_IMAGE
    try:
        headers = {"Authorization": os.environ['PEXELS_API_KEY']}
        pexels_resp = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": search_keyword.strip(), "per_page": 1},
            headers=headers,
            timeout=20,
        )
        pexels_resp.raise_for_status()
        data = pexels_resp.json()
        photos = data.get('photos') or []
        if photos:
            image_url = photos[0]['src']['large']
    except Exception:
        pass

    return image_url


def generate_description(title):
    prompt = (
        f"Write exactly 2 sentences for Cleveland residents for a plumbing post titled '{title}'. "
        "No XML. Plain text only."
    )
    resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    return resp.text.strip()


def build_item_xml(title, description_text, image_url):
    pub_date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    guid = f"lakefrontleakanddrain.com/post/{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    return f"""    <item>
      <title>{escape(title)}</title>
      <link>{DEFAULT_LINK}</link>
      <guid isPermaLink="false">{guid}</guid>
      <pubDate>{pub_date}</pubDate>
      <description><![CDATA[{description_text}]]></description>
      <enclosure url="{escape(image_url)}" length="0" type="image/jpeg" />
    </item>"""


def title_exists(feed_text, title):
    return f"<title>{escape(title)}</title>" in feed_text


def inject_item_at_top(feed_text, item_xml):
    first_item_pos = feed_text.find('<item>')
    if first_item_pos != -1:
        return feed_text[:first_item_pos] + item_xml + "\n\n" + feed_text[first_item_pos:]

    insert_pos = feed_text.rfind('</channel>')
    if insert_pos == -1:
        raise ValueError("Could not find a valid insertion point in feed.xml")

    return feed_text[:insert_pos] + item_xml + "\n\n" + feed_text[insert_pos:]


def main():
    title, search_keyword = generate_topic()
    image_url = get_image_url(search_keyword)
    description_text = generate_description(title)

    with open(FEED_PATH, 'r', encoding='utf-8') as f:
        feed = f.read()

    if title_exists(feed, title):
        print(f"Skipped duplicate title: {title}")
        return

    new_item = build_item_xml(title, description_text, image_url)
    updated_feed = inject_item_at_top(feed, new_item)

    with open(FEED_PATH, 'w', encoding='utf-8') as f:
        f.write(updated_feed)

    print(f"Added new item at top: {title}")


if __name__ == '__main__':
    main()
