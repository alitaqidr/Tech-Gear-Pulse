import os
import base64
import requests
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from google import genai

# ==========================================
# BOT 1: RESEARCH & TREND SCOUT
# ==========================================
def research_bot_scout(topic: str) -> str:
    print(f"[Bot 1 - Scout]: Gathering live trends for '{topic}'...")
    try:
        encoded_query = urllib.parse.quote(topic)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        results = []
        for item in root.findall('.//item')[:4]:
            title = item.find('title').text if item.find('title') is not None else "No Title"
            results.append(f"- {title}")
        
        scout_data = "\n".join(results) if results else "No recent breaking news found."
        print(f"[Bot 1 - Scout]: Successfully gathered {len(results)} headline trends.")
        return scout_data
    except Exception as e:
        print(f"[Bot 1 - Scout]: Notice during fetch - {str(e)}")
        return "Standard evergreen market trends apply."

# ==========================================
# BOT 2: WRITER & AFFILIATE MONETIZER
# ==========================================
def writer_bot_publish(topic: str, research_data: str):
    print(f"[Bot 2 - Writer]: Drafting SEO-optimized article and injecting monetization...")
    
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    prompt = f"""
    You are an expert tech and consumer goods copywriter. 
    Write a comprehensive, engaging, SEO-optimized blog post in Markdown about: {topic}.
    Incorporate these recent news headlines/trends discovered by research:
    {research_data}
    
    Include an appealing title, an introduction, key subheadings (H2, H3), pros/cons or key takeaways, and a conclusion.
    """
    
    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents=prompt
    )
    
    raw_content = response.text
    
    # Inject multi-marketplace affiliate links & banners
    encoded_topic = urllib.parse.quote(topic)
    amazon_tag = os.getenv("AMAZON_AFFILIATE_TAG", "yourtag-20")
    amazon_url = f"https://www.amazon.com/s?k={encoded_topic}&tag={amazon_tag}"

    ad_banner_block = f"""
---
<div align="center" style="padding: 18px; border: 2px solid #e0e0e0; border-radius: 10px; margin: 30px 0; background-color: #f8f9fa;">
  <p style="margin: 0; font-size: 0.8em; color: #777; letter-spacing: 1px; font-weight: bold;">SPONSORED PRODUCTS & MARKETPLACE DEALS</p>
  <h3 style="margin: 10px 0; color: #222;">🛒 Shop Trending Deals for "{topic}"</h3>
  <div style="display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; margin-top: 12px;">
    <a href="{amazon_url}" target="_blank" rel="nofollow sponsored" style="background-color: #FF9900; color: #111; padding: 8px 16px; text-decoration: none; font-weight: bold; border-radius: 5px;">Amazon Store →</a>
  </div>
</div>
---
"""
    monetized_content = raw_content + "\n\n" + ad_banner_block + "\n\n*Disclaimer: As an affiliate, this platform earns from qualifying purchases.*"
    
    # Save markdown backup
    os.makedirs('posts', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"posts/article_{timestamp}.md"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(monetized_content)
        
    print(f"[Bot 2 - Writer]: Successfully generated and saved article to {filename}")

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
    
    # Execute Bot 1
    research_insights = research_bot_scout(topic)
    
    # Execute Bot 2
    writer_bot_publish(topic, research_insights)

if __name__ == "__main__":
    run()
