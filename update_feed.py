import os
import requests
import re
import random
from google import genai
from datetime import datetime, timedelta # Fixed: Added timedelta here
from xml.sax.saxutils import escape

client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])

# CONFIGURATION
FEED_PATH = 'plumbing-tips.xml'
DEFAULT_LINK = 'https://lakefrontleakanddrain.com/blog/'
DEFAULT_IMAGE = 'https://lakefrontleakanddrain.com/logo.jpg'

def create_slug(title):
    """Turns 'Spring Sump Pump!' into 'spring-sump-pump'"""
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9 ]', '', slug) 
    slug = slug.strip().replace(' ', '-')
    return slug

def generate_topic():
    """Asks AI for a seasonal topic and a search keyword"""
    prompt = (
        "Invent a seasonal Cleveland plumbing blog topic. "
        "Output ONLY the Title and a highly descriptive 2-word image search keyword separated by a pipe. "
        "Example: Spring Sump Pump | flooded basement"
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
    """Picks a random image from Pexels to ensure variety"""
    image_url = DEFAULT_IMAGE
    try:
        headers = {"Authorization": os.environ['PEXELS_API_KEY']}
        pexels_resp = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": search_keyword.strip(), "per_page": 15},
            headers=headers,
            timeout=20,
        )
        pexels_resp.raise_for_status()
        data = pexels_resp.json()
        if data.get('photos'):
            random_photo = random.choice(data['photos'])
            image_url = random_photo['src']['large']
    except Exception as e:
        print(f"Image search failed: {e}")
    return image_url

def generate_description(title):
    """Asks AI to write the actual blog tip"""
    prompt = f"Write a 2-sentence helpful plumbing tip for Cleveland residents about '{title}'. Use a friendly, professional tone. Output ONLY the text."
    resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    return resp.text.strip()

def format_rss_item(title, image_url, description_text):
    """Formats the XML block with unique IDs and safe encoding"""
    # BACKDATE FIX: Subtract 6 hours so it's always in the past for Metricool
    past_time = datetime.utcnow() - timedelta(hours=6)
    pub_date = past_time.strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    slug = create_slug(title)
    unique_link = f"{DEFAULT_LINK}?post={slug}"
    
    # UNIQUE GUID: Added a version suffix to force Metricool to re-scan
    guid = f"{slug}-{datetime.utcnow().strftime('%Y%m%d')}-v2"
    
    safe_title = escape(title.replace('&amp;', '&'))
    safe_image = escape(image_url.replace('&amp;', '&'))
    
    return f"""    <item>
      <title>{safe_title}</title>
      <link>{unique_link}</link>
      <guid isPermaLink="false">{guid}</guid>
      <pubDate>{pub_date}</pubDate>
      <description><![CDATA[{description_text}]]></description>
      <enclosure url="{safe_image}" length="0" type="image/jpeg" />
    </item>"""

def main():
    title, search_keyword = generate_topic()
    image_url = get_image_url(search_keyword)
    description_text = generate_description(title)

    with open(FEED_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    full_text = "".join(lines)
    if f"<title>{escape(title)}</title>" in full_text:
        print(f"Skipped duplicate title: {title}")
        return

    new_item_xml = format_rss_item(title, image_url, description_text)

    new_content = []
    inserted = False
    for line in lines:
        if '<item>' in line and not inserted:
            new_content.append(f"{new_item_xml}\n\n")
            inserted = True
        new_content.append(line)

    if not inserted:
        for i, line in enumerate(new_content):
            if '</language>' in line or '</description>' in line:
                new_content.insert(i + 1, f"\n{new_item_xml}\n")
                inserted = True
                break

    with open(FEED_PATH, 'w', encoding='utf-8') as f:
        f.writelines(new_content)

    print(f"Success! Added to top: {title}")

if __name__ == "__main__":
    main()
