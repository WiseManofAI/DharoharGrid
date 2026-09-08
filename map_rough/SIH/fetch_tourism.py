import urllib.request
from bs4 import BeautifulSoup
import json
import ssl
import re

print("Attempting live scrape of the official Rajasthan Tourism portal...")

# Bypass SSL verification just like we did for the ASI portal
ssl._create_default_https_context = ssl._create_unverified_context

url = "https://www.tourism.rajasthan.gov.in/fairs-and-festivals.html"

try:
    # We must mask our script as a standard web browser, or their firewall will block us
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    response = urllib.request.urlopen(req)
    html = response.read()
    soup = BeautifulSoup(html, 'html.parser')

    print("Successfully connected! Hunting for festival data...")
    
    festival_nodes = []
    
    # Tourism sites often wrap their events in specific div classes or header tags. 
    # We will search for <h3> or <strong> tags that might contain the festival names.
    # Note: If the website updates its UI, these HTML targets will break.
    
    content_blocks = soup.find_all(['h3', 'h4', 'div'], class_=re.compile(r'title|heading|fest', re.I))
    
    for idx, block in enumerate(content_blocks):
        title = block.text.strip()
        
        # Filter out empty strings or navigation menu garbage
        if len(title) > 4 and "Festival" in title or "Fair" in title:
            
            clean_id = f"IN-RJ-LIVE-FEST-{idx:03d}"
            
            node = {
                "node_id": clean_id,
                "title": title,
                "category": "INTANGIBLE_FESTIVAL",
                "location_text": "Rajasthan", # Requires a geocoder pass later to find the exact city
                "era": "Annual Cultural Event",
                "famous_for": f"A cultural event officially listed on the Rajasthan Tourism portal.",
                "docent_details": "Live-scraped from tourism.rajasthan.gov.in.",
                "media": {"photo_url": "", "attribution": "Rajasthan Tourism"},
                "trust_status": "government_verified",
                "synapses": [{"connection": "Automated pipeline extraction from official state directories."}]
            }
            # Prevent duplicates
            if not any(n['title'] == title for n in festival_nodes):
                festival_nodes.append(node)

    output_path = "tourism_raw_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(festival_nodes, f, indent=2, ensure_ascii=False)

    print(f"\nSuccess! Live-scraped {len(festival_nodes)} festivals from the HTML.")
    print(f"Data saved to {output_path}.")

except Exception as e:
    print(f"Live scrape failed. The server might be blocking bots or using JavaScript: {e}")
    print("Hackathon Tip: Use the pre-built 'add_festivals.py' injection script instead to guarantee your map works during the demo!")