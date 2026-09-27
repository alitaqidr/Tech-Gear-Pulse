import os
import re
import sys
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
import praw
from google import genai

# ==========================================
# BOT 1: RESEARCH & TREND SCOUT
# ==========================================
def research_bot_scout(topic: str) -> str:
    print(f"[Bot 1 - Scout]: Gathering live trends for '{topic}'...")
    try:
        encoded_query = urllib.parse.quote(topic)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        results = []
        for item in root.findall('.//item')[:4]:
            title_elem = item.find('title')
            if title_elem is not None and title_elem.text:
                results.append(f"- {title_elem.text}")
        
        if results:
            scout_data = "\n".join(results)
            print(f"[Bot 1 - Scout]: Successfully gathered {len(results)} headline trends.")
            return scout_data
        else:
            print("[Bot 1 - Scout]: No items found in RSS feed. Using default context.")
            return f"Current industry innovations and top consumer demand trends for {topic}."

    except Exception as e:
        print(f"[Bot 1 - Scout]: RSS fetch warning ({str(e)}). Falling back to evergreen context.")
        return f"Current industry innovations and top consumer demand trends for {topic}."

# ==========================================
# BOT 2: WRITER & AFFILIATE MONETIZER
# ==========================================
def get_best_available_model(client: genai.Client) -> str:
    """Dynamically queries the API to find an active text-generation model."""
    try:
        print("[Bot 2 - Writer]: Querying API for available models...")
        available_models = [m.name for m in client.models.list() if "generateContent" in getattr(m, "supported_generation_methods", [])]
        
        clean_models = [m.replace("models/", "") for m in available_models]
        print(f"[Bot 2 - Writer]: Found active models: {clean_models}")
        
        for target in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash", "gemini-2.5-pro", "gemini-pro"]:
            for model in clean_models:
                if target in model:
                    return model
                    
        if clean_models:
            return clean_models[0]
    except Exception as e:
        print(f"[Bot 2 - Writer]: Model auto-discovery warning ({str(e)}). Defaulting to 'gemini-2.5-flash'.")
        
    return "gemini-2.5-flash"

def publish_to_hashnode(title: str, markdown_content: str):
    """Publishes the article directly to Hashnode."""
    token = os.getenv("HASHNODE_TOKEN")
    pub_id = os.getenv("HASHNODE_PUBLICATION_ID")

    if not token or not pub_id:
        print("[Hashnode]: Skipped (HASHNODE_TOKEN or HASHNODE_PUBLICATION_ID missing).")
        return

    url = "https://gql.hashnode.com"
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }

    query = """
    mutation PublishPost($input: PublishPostInput!) {
      publishPost(input: $input) {
        post {
          id
          title
          url
        }
      }
    }
    """

    variables = {
        "input": {
            "title": title,
            "contentMarkdown": markdown_content,
            "publicationId": pub_id,
            "tags": []
        }
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps({"query": query, "variables": variables}).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req) as resp:
            res_data = json.loads(resp.read().decode())
            if "errors" in res_data:
                print(f"[Hashnode Error]: {res_data['errors']}")
            else:
                post_url = res_data.get("data", {}).get("publishPost", {}).get("post", {}).get("url")
                print(f"[Hashnode]: Article published successfully -> {post_url}")
    except Exception as e:
        print(f"[Hashnode Exception]: {str(e)}")


def publish_to_reddit(title: str, markdown_content: str):
    """Posts the article to your chosen Subreddit."""
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    username = os.getenv("REDDIT_USERNAME")
    password = os.getenv("REDDIT_PASSWORD")
    subreddit_name = os.getenv("REDDIT_SUBREDDIT")

    if not all([client_id, client_secret, username, password, subreddit_name]):
        print("[Reddit]: Skipped (Reddit credentials incomplete in environment).")
        return

    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            username=username,
            password=password,
            user_agent="TechGearPulseBot/1.0 by /u/" + username
        )

        subreddit = reddit.subreddit(subreddit_name)
        submission = subreddit.submit(title, selftext=markdown_content)
        print(f"[Reddit]: Article published to r/{subreddit_name} -> {submission.url}")
    except Exception as e:
        print(f"[Reddit Exception]: {str(e)}")

def writer_bot_publish(topic: str, research_data: str):
    print(f"[Bot 2 - Writer]: Initializing Gemini Client...")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[Error]: GEMINI_API_KEY environment variable is missing or empty!")
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    
    selected_model = get_best_available_model(client)
    print(f"[Bot 2 - Writer]: Selected Model -> '{selected_model}'")
    
    prompt = f"""
    You are an expert tech and consumer goods copywriter. 
    Write a comprehensive, engaging, SEO-optimized blog post in Markdown about: {topic}.
    Incorporate these recent news headlines/trends discovered by research:
    {research_data}
    
    Include an appealing title starting with '# ', an introduction, key subheadings (H2, H3), pros/cons or key takeaways, and a conclusion.
    """

    try:
        response = client.models.generate_content(
            model=selected_model,
            contents=prompt
        )
        if not response or not response.text:
            print("[Error]: Model returned an empty response.")
            sys.exit(1)
        raw_content = response.text
    except Exception as e:
        print(f"[Error]: Content generation failed with model '{selected_model}': {str(e)}")
        sys.exit(1)

    encoded_topic = urllib.parse.quote(topic)
    
    # 1. Amazon Link
    amazon_tag = os.getenv("AMAZON_AFFILIATE_TAG", "yourtag-20")
    amazon_url = f"https://www.amazon.com/s?k={encoded_topic}&tag={amazon_tag}"
    
    # 2. eBay Link (Using official EPN tracking parameters)
    ebay_campaign_id = os.getenv("EBAY_CAMPAIGN_ID", "")
    target_ebay = f"https://www.ebay.com/sch/i.html?_nkw={encoded_topic}"
    if ebay_campaign_id:
        ebay_url = f"{target_ebay}&mkevt=1&mkcid=1&mkrid=711-53200-19255-0&campid={ebay_campaign_id}&toolid=10001"
    else:
        ebay_url = target_ebay

    # 3. Temu Link
    temu_code = os.getenv("TEMU_AFFILIATE_CODE", "")
    temu_url = f"https://www.temu.com/search_result.html?search_key={encoded_topic}"
    if temu_code:
        temu_url += f"&refer_code={temu_code}"

    # 4. Daraz Link
    daraz_affiliate_id = os.getenv("DARAZ_AFFILIATE_ID", "")
    daraz_url = f"https://www.daraz.pk/catalog/?q={encoded_topic}"
    if daraz_affiliate_id:
        daraz_url += f"&aff_id={daraz_affiliate_id}"

    # Google AdSense Code
    adsense_client = os.getenv("ADSENSE_CLIENT_ID", "ca-pub-0000000000000000")
    adsense_slot = os.getenv("ADSENSE_SLOT_ID", "0000000000")
    adsense_block = f"""
<div align="center" style="margin: 25px 0;">
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={adsense_client}" crossorigin="anonymous"></script>
  <ins class="adsbygoogle"
       style="display:block"
       data-ad-client="{adsense_client}"
       data-ad-slot="{adsense_slot}"
       data-ad-format="auto"
       data-full-width-responsive="true"></ins>
  <script>
       (adsbygoogle = window.adsbygoogle || []).push({{}});
  </script>
</div>
"""

    # Visual Poster Banner Block
    ad_banner_block = f"""
---
<div align="center" style="padding: 20px; border: 1px solid #e1e4e8; border-radius: 12px; margin: 30px 0; background: #ffffff; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
  <p style="margin: 0 0 10px 0; font-size: 0.8em; color: #888; letter-spacing: 1.5px; font-weight: bold; text-transform: uppercase;">Featured Marketplace Deals</p>
  <h3 style="margin: 0 0 20px 0; color: #1a1a1a;">🛒 Shop Trending Deals for "{topic}"</h3>
  
  <div style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap; max-width: 900px;">
    
    <!-- Amazon Poster -->
    <a href="{amazon_url}" target="_blank" rel="nofollow sponsored" style="text-decoration: none; color: inherit; width: 160px; border: 1px solid #eee; border-radius: 8px; overflow: hidden; background: #fff;">
      <img src="https://images.unsplash.com/photo-1523474253046-8cd2748b5fd2?w=400&q=80" alt="Amazon Deals" style="width: 100%; height: 110px; object-fit: cover; display: block;" />
      <div style="padding: 10px; background: #FF9900; text-align: center; color: #111; font-weight: bold; font-size: 0.9em;">
        Amazon →
      </div>
    </a>

    <!-- eBay Poster -->
    <a href="{ebay_url}" target="_blank" rel="nofollow sponsored" style="text-decoration: none; color: inherit; width: 160px; border: 1px solid #eee; border-radius: 8px; overflow: hidden; background: #fff;">
      <img src="https://images.unsplash.com/photo-1607082348824-0a96f2a4b9da?w=400&q=80" alt="eBay Deals" style="width: 100%; height: 110px; object-fit: cover; display: block;" />
      <div style="padding: 10px; background: #0064D2; text-align: center; color: #fff; font-weight: bold; font-size: 0.9em;">
        eBay →
      </div>
    </a>

    <!-- Temu Poster -->
    <a href="{temu_url}" target="_blank" rel="nofollow sponsored" style="text-decoration: none; color: inherit; width: 160px; border: 1px solid #eee; border-radius: 8px; overflow: hidden; background: #fff;">
      <img src="https://images.unsplash.com/photo-1472851294608-062f824d29cc?w=400&q=80" alt="Temu Deals" style="width: 100%; height: 110px; object-fit: cover; display: block;" />
      <div style="padding: 10px; background: #FB7701; text-align: center; color: #fff; font-weight: bold; font-size: 0.9em;">
        Temu →
      </div>
    </a>

    <!-- Daraz Poster -->
    <a href="{daraz_url}" target="_blank" rel="nofollow sponsored" style="text-decoration: none; color: inherit; width: 160px; border: 1px solid #eee; border-radius: 8px; overflow: hidden; background: #fff;">
      <img src="https://images.unsplash.com/photo-1555529669-e69e7aa0ba9a?w=400&q=80" alt="Daraz Deals" style="width: 100%; height: 110px; object-fit: cover; display: block;" />
      <div style="padding: 10px; background: #f57224; text-align: center; color: #fff; font-weight: bold; font-size: 0.9em;">
        Daraz →
      </div>
    </a>

  </div>
</div>
---
"""

    title_match = re.search(r"^#\s+(.*)", raw_content, re.MULTILINE)
    article_title = title_match.group(1).replace('"', "'") if title_match else "Tech Gear Pulse Update"

    today_date = datetime.now().strftime('%Y-%m-%d')
    timestamp_id = datetime.now().strftime('%H%M%S')
    
    yaml_header = f"""---
layout: post
title: "{article_title}"
date: {today_date}
tags: [tech, gadgets, reviews]
---

"""

    full_content = (
        yaml_header 
        + raw_content 
        + "\n\n" 
        + adsense_block 
        + "\n\n" 
        + ad_banner_block 
        + "\n\n*Disclaimer: As an affiliate, this platform earns from qualifying purchases.*"
    )
    
    slugified_title = re.sub(r'[^a-zA-Z0-9]', '-', article_title.lower())[:30].strip('-')
    os.makedirs('_posts', exist_ok=True)
    filename = f"_posts/{today_date}-{slugified_title}-{timestamp_id}.md"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(full_content)
        
    print(f"[Bot 2 - Writer]: Article successfully saved to local website folder '{filename}'.")

    # Publish externally to Hashnode and Reddit
    publish_to_hashnode(article_title, raw_content + "\n\n" + ad_banner_block)
    publish_to_reddit(article_title, raw_content + "\n\n" + ad_banner_block)

# ==========================================
# PIPELINE ORCHESTRATION
# ==========================================
TOPIC_SCHEDULE = {
    0: "Smart Home Automation, Desk Setups, and Workspace Gadgets",
    1: "Fitness Tech, Smartwatches, and Outdoor Hiking Gear Trends",
    2: "Home Office Cybersecurity, Mesh Wi-Fi, and Network Storage Hardware",
    3: "Portable Power Stations, EV Chargers, and Solar Energy Tech",
    4: "Gaming PC Hardware, OLED Gaming Monitors, and Ergonomic Chairs",
    5: "Smart Kitchen Gadgets, Air Fryers, and Automated Home Appliances",
    6: "Noise-Canceling Headphones, Mobile Accessories, and Audio Tech"
}

def run():
    day_of_week = datetime.now().weekday()
    topic = os.getenv("PUBLISH_TOPIC", TOPIC_SCHEDULE.get(day_of_week, "Smart Home Automation"))
    print(f"--- Starting Publishing Pipeline for Topic: '{topic}' ---")
    
    research_insights = research_bot_scout(topic)
    writer_bot_publish(topic, research_insights)

if __name__ == "__main__":
    run()
