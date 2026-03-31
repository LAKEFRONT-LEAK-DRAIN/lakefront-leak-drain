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

# THE DOUBLE-LINE SCRUBBER
new_item = new_item.replace('&amp;', '&') 
new_item = new_item.replace('&', '&amp;')

# 4. ✨ CORRECTED INJECTION LOGIC - Insert BEFORE first <item>
with open('feed.xml', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the position of the first <item> tag
first_item_pos = content.find('<item>')

if first_item_pos != -1:
    # Insert the new item right before the first <item>
    new_content = content[:first_item_pos] + new_item + '\n\n' + content[first_item_pos:]
else:
    # Fallback: append at the end of channel if no item found
    new_content = content.replace('</channel>', f'{new_item}\n\n</channel>')

with open('feed.xml', 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"✅ Verified: '{title}' added to the TOP of the feed.")
