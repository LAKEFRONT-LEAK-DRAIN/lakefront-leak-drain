import os
from google import genai
from datetime import datetime

client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])

# Format today's date for the RSS feed
today_str = datetime.utcnow().strftime('%a, %d %b %Y 10:00:00 GMT')

prompt = f"""
You are the Chief Marketing Officer for Lakefront Leak & Drain, a plumbing company in Cleveland, Ohio.
Invent a highly engaging, brand new topic for a plumbing tip or service that homeowners or property managers in Cleveland need right now (think about seasonal weather, current events, or common emergencies).

Write a valid RSS <item> block for this new post. 
Use 'https://lakefrontleakanddrain.com/' for the link.
Include <media:content url="https://drive.google.com/uc?export=download&id=1e8xTL1hnn37_a_XL9Dbi_glnrAWY6PV2" medium="video" />
Include <enclosure url="https://lakefrontleakanddrain.com/logo.jpg" length="0" type="image/jpeg" />
Use this exact date for the pubDate: {today_str}

CRITICAL: Output ONLY the raw <item>...</item> XML block. Do not include markdown formatting like ```xml. Just the code.
"""

# Generate the content using our confirmed working model
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=prompt
)
new_item = response.text.strip()

# Clean up any markdown
if new_item.startswith('```xml'):
    new_item = new_item[6:]
if new_item.startswith('```'):
    new_item = new_item[3:]
if new_item.endswith('```'):
    new_item = new_item[:-3]
new_item = new_item.strip()

# Open the existing feed
with open('feed.xml', 'r', encoding='utf-8') as f:
    feed = f.read()
    
# Surgically inject the new post right before the </channel> closing tag
insert_pos = feed.rfind('</channel>')
if insert_pos != -1:
    updated_feed = feed[:insert_pos] + '    ' + new_item + '\n\n' + feed[insert_pos:]
    with open('feed.xml', 'w', encoding='utf-8') as f:
        f.write(updated_feed)
