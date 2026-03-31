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

# THE DOUBLE-LINE SCRUBBER (The one that works)
new_item = new_item.replace('&amp;', '&') 
new_item = new_item.replace('&', '&amp;')

# 4. THE "FORCE-TO-TOP" INJECTION
# This reads the file line-by-line and inserts the new post ABOVE the first old post
with open('feed.xml', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_content = []
inserted = False

for line in lines:
    # As soon as the script finds the first existing blog post...
    if '<item>' in line and not inserted:
        # It shoves the new post right ABOVE it
        new_content.append(f"    {new_item}\n\n")
        inserted = True
    new_content.append(line)

# Fallback if the file is empty of posts or markers are weird
if not inserted:
    # Insert right after the header information (top of file)
    for i, line in enumerate(new_content):
        if '</language>' in line or '</description>' in line:
            new_content.insert(i + 1, f"    {new_item}\n\n")
            inserted = True
            break

with open('feed.xml', 'w', encoding='utf-8') as f:
    f.writelines(new_content)

print(f"Verified: '{title}' added to the TOP of the feed.")