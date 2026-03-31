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

# 4. ✨ FIXED INJECTION LOGIC
with open('feed.xml', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_content = []
inserted = False

for line in lines:
    new_content.append(line)  # ⬅️ Add the current line FIRST
    
    # Insert AFTER <channel> tag or BEFORE first <item>
    if not inserted:
        # Option 1: Insert after opening <channel> tag
        if '<channel>' in line:
            new_content.append(f"{new_item}\n\n")
            inserted = True
        # Option 2: Insert before first <item> (backup method)
        elif '<item>' in line:
            # Remove the just-added line, insert new item, then re-add it
            new_content.pop()
            new_content.append(f"{new_item}\n\n")
            new_content.append(line)
            inserted = True

# Fallback if no insertion point found
if not inserted:
    for i, line in enumerate(new_content):
        if '</description>' in line or '</language>' in line:
            new_content.insert(i + 1, f"{new_item}\n\n")
            break

with open('feed.xml', 'w', encoding='utf-8') as f:
    f.writelines(new_content)

print(f"✅ Verified: '{title}' added to the TOP of the feed.")
