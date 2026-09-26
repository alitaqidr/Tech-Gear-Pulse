import os
import sys
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
        
        # Strip 'models/' prefix if present in SDK return
        clean_models = [m.replace("models/", "") for m in available_models]
        print(f"[Bot 2 - Writer]: Found active models: {clean_models}")
        
        # Priority order: preferred flash models -> preferred pro models -> any available model
        for target in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash", "gemini-2.5-pro", "gemini-pro"]:
            for model in clean_models:
                if target in model:
                    return model
                    
        if clean_models:
            return clean_models[0]
    except Exception as e:
        print(f"[Bot 2 - Writer]: Model auto-discovery warning ({str(e)}). Defaulting to 'gemini-2.5-flash'.")
        
    return "gemini-2.5-flash"

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
    
    Include an appealing title, an introduction, key subheadings (H2, H3), pros/cons or key takeaways, and a conclusion.
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

    # Multi-marketplace links
    encoded_topic = urllib.parse.quote(topic)
    amazon_tag = os.getenv("AMAZON_AFFILIATE_TAG", "yourtag-20")
    amazon_url = f"https://www.amazon.com/s?k={encoded_topic}&tag={amazon_tag}"
    
    ebay_campaign_id = os.getenv("EBAY_CAMPAIGN_ID", "")
    ebay_url = f"https://www.ebay.com/sch/i.html?_nkw={encoded_topic}"
    if ebay_campaign_id:
        ebay_url += f"&mkcid=1&mkrid=711-53200-19255-0&siteid=0&campid={ebay_campaign_id}"

    walmart_url = f"https://www.walmart.com/search?q={encoded_topic}"
    temu_url = f"https://www.temu.com/search_result.html?search_key={encoded_topic}"

    ad_banner_block = f"""
---
<div align="center" style="padding: 18px; border: 2px solid #e0e0e0; border-radius: 10px; margin: 30px 0; background-color: #f8f9fa;">
  <p style="margin: 0; font-size: 0.8em; color: #777; letter-spacing: 1px; font-weight: bold;">SPONSORED PRODUCTS & MARKETPLACE DEALS</p>
  <h3 style="margin: 10px 0; color: #222;">🛒 Shop Trending Deals for "{topic}"</h3>
  <div style="display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; margin-top: 12px;">
    <a href="{amazon_url}" target="_blank" rel="nofollow sponsored" style="background-color: #FF9900; color: #111; padding: 8px 16px; text-decoration: none; font-weight: bold; border-radius: 5px;">Amazon →</a>
    <a href="{ebay_url}" target="_blank" rel="nofollow sponsored" style="background-color: #0064D2; color: #fff; padding: 8px 16px; text-decoration: none; font-weight: bold; border-radius: 5px;">eBay →</a>
    <a href="{walmart_url}" target="_blank" rel="nofollow sponsored" style="background-color: #0071DC; color: #fff; padding: 8px 16px; text-decoration: none; font-weight: bold; border-radius: 5px;">Walmart →</a>
    <a href="{temu_url}" target="_blank" rel="nofollow sponsored" style="background-color: #FB7701; color: #fff; padding: 8px 16px; text-decoration: none; font-weight: bold; border-radius: 5px;">Temu →</a>
  </div>
</div>
---
"""
    monetized_content = raw_content + "\n\n" + ad_banner_block + "\n\n*Disclaimer: As an affiliate, this platform earns from qualifying purchases.*"
    
    os.makedirs('posts', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"posts/article_{timestamp}.md"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(monetized_content)
        
    print(f"[Bot 2 - Writer]: Article successfully generated and saved to '{filename}'.")

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
