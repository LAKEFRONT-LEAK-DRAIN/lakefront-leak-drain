import os
import requests
from google import genai
from datetime import datetime

client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])

# 1. Generate Topic
topic_prompt = "Invent a seasonal Cleveland plumbing blog topic. Output ONLY the Title and a 2-word image search keyword separated by a pipe. Example: Spring Sump Pump | sump pump"
resp = client.models.generate_content(model='gemini-2.5-flash', contents=topic_prompt)

try:
    title, search_keyword = resp.text.strip().split('|')
except:
    title = resp.text.strip()
    search_keyword = "plumbing"

# 2. Get Image
image_url = "https://lakefrontleakanddrain.com/logo.jpg"
try:
    headers = {"Authorization": os.environ['PEXELS_API_KEY']}
    pexels_resp = requests.get(f"https://api.pexels.com/v1/search?query={search_keyword.strip()}&per_page=1", headers=headers)
    image_url = pexels_resp.json()['photos'][0]['src']['large']
except:
    pass

# 3. Create Item
today_str = datetime.utcnow().strftime('%a, %d %b %Y 10:00:00 GMT')
xml_prompt = f"Write a valid RSS <item> block for a post titled '{title}'. Use 'https://lakefrontleakanddrain.com/' for link. Use {image_url} for enclosure. Include 2 sentences for Cleveland residents. Output ONLY raw XML."

final_resp = client.models.generate_content(model='gemini-2.5-flash', contents=xml_prompt)
new_item = final_resp.text.strip().replace('```xml', '').replace('```', '').strip()

# SCRUBBER: This fixes the 'EntityRef' error by encoding all ampersands properly
# We do this twice to ensure we don't 'double-encode' existing entities
new_item = new_item.replace('&amp;', '&') 
new_item = new_item.replace('&', '&amp;')

# 4. Inject (TOP INSERTION)
with open('feed.xml', 'r', encoding='utf-8') as f:
    feed = f.read()

# Look for the header tags to find the top of the list
markers = ['</language>', '</description>', '</link>', '<channel>']
insert_pos = -1

for m in markers:
    pos = feed.find(m)
    if pos != -1:
        insert_pos = pos + len(m)
        break

if insert_pos != -1:
    # Build the feed: Metadata + New Post + Existing Posts
    updated_feed = feed[:insert_pos] + '\n\n    ' + new_item + feed[insert_pos:]
    with open('feed.xml', 'w', encoding='utf-8') as f:
        f.write(updated_feed)
    print(f"Success! Newest post '{title}' is now at the top.")
else:
    print("Error: Could not find a valid insertion point.")