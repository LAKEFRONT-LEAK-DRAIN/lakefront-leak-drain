import os
import requests
import re
import random
from google import genai
from datetime import datetime, timedelta
from xml.sax.saxutils import escape

client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])

# CONFIGURATION
FEED_PATH = 'feed.xml'
DEFAULT_LINK = 'https://lakefrontleakanddrain.com/'
DEFAULT_IMAGE = 'https://lakefrontleakanddrain.com/logo.jpg'

def get_image_length(image_url):
    """Get actual image file size, fallback to reasonable default."""
    try:
        response = requests.head(image_url, timeout=5)
        content_length = response.headers.get('Content-Length')
        if content_length and int(content_length) > 0:
            return content_length
    except Exception as e:
        print(f"Could not fetch image size: {e}")
    
    return "150000"

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

def get_next_post_id(lines):
    """Get the next post ID by finding the highest existing ID"""
    max_id = 32
    for line in lines:
        if '<wp:post_id>' in line:
            try:
                post_id = int(line.split('<wp:post_id>')[1].split('</wp:post_id>')[0])
                max_id = max(max_id, post_id)
            except:
                pass
    return max_id + 1

def format_rss_item(title, image_url, description_text, post_id):
    """Formats XML block - EXACT WordPress format with enclosure for images"""
    past_time = datetime.utcnow() - timedelta(hours=6)
    pub_date = past_time.strftime('%a, %d %b %Y %H:%M:%S +0000')
    post_date = past_time.strftime('%Y-%m-%d %H:%M:%S')
    
    slug = create_slug(title)
    
    # WordPress-style GUID, but link to actual HTML page
    guid = f"https://lakefrontleakanddrain.com/?p={post_id}"
    link = f"https://lakefrontleakanddrain.com/blog/{slug}.html"
    
    safe_title = title.replace('&', '&amp;')
    safe_image = image_url.replace('&', '&amp;')
    
    image_length = get_image_length(image_url)
    
    content_html = f"""<!-- wp:paragraph -->
<p>{description_text}</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>👉 Visit our website:<br><a href="https://lakefrontleakanddrain.com">https://lakefrontleakanddrain.com</a></p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>📞 216-505-7765</p>
<!-- /wp:paragraph -->"""
    
    return f"""	<item>
		<title><![CDATA[{safe_title}]]></title>
		<link>{link}</link>
		<pubDate>{pub_date}</pubDate>
		<dc:creator><![CDATA[lakefrontleakanddrain]]></dc:creator>
		<guid isPermaLink="false">{guid}</guid>
		<description></description>
		<content:encoded><![CDATA[{content_html}]]></content:encoded>
		<excerpt:encoded><![CDATA[]]></excerpt:encoded>
		<wp:post_id>{post_id}</wp:post_id>
		<wp:post_date><![CDATA[{post_date}]]></wp:post_date>
		<wp:post_date_gmt><![CDATA[{post_date}]]></wp:post_date_gmt>
		<wp:post_modified><![CDATA[{post_date}]]></wp:post_modified>
		<wp:post_modified_gmt><![CDATA[{post_date}]]></wp:post_modified_gmt>
		<wp:comment_status><![CDATA[open]]></wp:comment_status>
		<wp:ping_status><![CDATA[open]]></wp:ping_status>
		<wp:post_name><![CDATA[{slug}]]></wp:post_name>
		<wp:status><![CDATA[publish]]></wp:status>
		<wp:post_parent>0</wp:post_parent>
		<wp:menu_order>0</wp:menu_order>
		<wp:post_type><![CDATA[post]]></wp:post_type>
		<wp:post_password><![CDATA[]]></wp:post_password>
		<wp:is_sticky>0</wp:is_sticky>
										<category domain="post_tag" nicename="cleveland-plumbing"><![CDATA[CLEVELAND PLUMBING]]></category>
		<category domain="post_tag" nicename="plumbing-tips"><![CDATA[PLUMBING TIPS]]></category>
		<category domain="post_tag" nicename="drain-cleaning"><![CDATA[DRAIN CLEANING]]></category>
		<category domain="category" nicename="uncategorized"><![CDATA[Uncategorized]]></category>
						<enclosure url="{safe_image}" length="{image_length}" type="image/jpeg" />
		<wp:postmeta>
		<wp:meta_key><![CDATA[_last_editor_used_jetpack]]></wp:meta_key>
		<wp:meta_value><![CDATA[block-editor]]></wp:meta_value>
		</wp:postmeta>
							</item>"""

def generate_blog_page(title, slug, image_url, description_text, post_id):
    """Generate individual HTML page for blog post"""
    
    safe_title = escape(title.replace('&amp;', '&'))
    safe_image = escape(image_url.replace('&amp;', '&'))
    safe_description = escape(description_text.replace('&amp;', '&'))
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{safe_title} - Lakefront Leak & Drain</title>
    
    <!-- Open Graph Meta Tags -->
    <meta property="og:title" content="{safe_title}">
    <meta property="og:description" content="{safe_description}">
    <meta property="og:image" content="{safe_image}">
    <meta property="og:url" content="https://lakefrontleakanddrain.com/blog/{slug}.html">
    <meta property="og:type" content="article">
    
    <!-- Twitter Meta Tags -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{safe_title}">
    <meta name="twitter:description" content="{safe_description}">
    <meta name="twitter:image" content="{safe_image}">
</head>
<body>
    <header>
        <a href="/">Lakefront Leak & Drain</a>
    </header>
    
    <main>
        <article>
            <h1>{safe_title}</h1>
            <img src="{safe_image}" alt="{safe_title}" style="max-width: 100%; height: auto;">
            <p>{safe_description}</p>
            <p>👉 Visit our website: <a href="https://lakefrontleakanddrain.com">lakefrontleakanddrain.com</a></p>
            <p>📞 216-505-7765</p>
        </article>
        <a href="/blog/">← Back to all tips</a>
    </main>
</body>
</html>"""
    
    # Write HTML file
    blog_dir = 'blog'
    if not os.path.exists(blog_dir):
        os.makedirs(blog_dir)
    
    with open(f'{blog_dir}/{slug}.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Generated blog page: blog/{slug}.html")

def main():
    title, search_keyword = generate_topic()
    image_url = get_image_url(search_keyword)
    description_text = generate_description(title)

    with open(FEED_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    full_text = "".join(lines)
    if f"<title><![CDATA[{title}]]></title>" in full_text:
        print(f"Skipped duplicate title: {title}")
        return

    post_id = get_next_post_id(lines)
    slug = create_slug(title)
    
    # Generate HTML blog page
    generate_blog_page(title, slug, image_url, description_text, post_id)
    
    # Generate RSS item
    new_item_xml = format_rss_item(title, image_url, description_text, post_id)

    new_content = []
    inserted = False
    
    for line in lines:
        new_content.append(line)
        if '<generator>' in line and not inserted:
            new_content.append(f"\n{new_item_xml}\n")
            inserted = True

    if not inserted:
        new_content = []
        for line in lines:
            if '</channel>' in line:
                new_content.append(f"{new_item_xml}\n\n")
                inserted = True
            new_content.append(line)

    with open(FEED_PATH, 'w', encoding='utf-8') as f:
        f.writelines(new_content)

    print(f"Success! Added: {title} (ID: {post_id})")

if __name__ == "__main__":
    main()