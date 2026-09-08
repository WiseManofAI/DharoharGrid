import urllib.request
from bs4 import BeautifulSoup
import json
import ssl
import re

print("Re-scraping Rajasthan Tourism with clean title/description separation...")

ssl._create_default_https_context = ssl._create_unverified_context
url = "https://www.tourism.rajasthan.gov.in/fairs-and-festivals.html"

try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    response = urllib.request.urlopen(req)
    soup = BeautifulSoup(response.read(), 'html.parser')

    festival_nodes = []
    
    # Target cards or containers that usually hold individual festival items
    # Looking for heading tags inside structural blocks
    cards = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'card|item|fest|event', re.I))
    
    if not cards:
        # Fallback: grab all h2 or h3 tags directly if cards aren't found
        cards = soup.find_all(['h2', 'h3'])

    for idx, card in enumerate(cards):
        title_el = card.find(['h3', 'h4', 'a', 'strong'])
        desc_el = card.find(['p', 'span'])
        
        raw_title = title_el.text.strip() if title_el else card.text.strip()
        raw_desc = desc_el.text.strip() if desc_el else "A cultural event officially listed on the Rajasthan Tourism portal."
        
        # Clean up the title: Keep only the actual name (e.g., drop paragraphs or long dates)
        # Remove anything containing years like 2027 or massive sentence blocks
        if len(raw_title) > 50 or "FESTIVALS" in raw_title.upper() and len(raw_title.split()) > 6:
            continue
            
        if "Festival" in raw_title or "Fair" in raw_title or "Utsav" in raw_title:
            clean_title = re.sub(r'[-–—]\s*\d{4}.*', '', raw_title).strip() # Remove "- 2027..."
            clean_title = clean_title.replace("FESTIVALS", "").strip()
            
            if len(clean_title) < 3: 
                continue

            clean_id = f"IN-RJ-CLEAN-FEST-{idx:03d}"
            
            node = {
                "node_id": clean_id,
                "title": clean_title,
                "category": "INTANGIBLE_FESTIVAL",
                "location_text": "Rajasthan",
                "era": "Annual Cultural Event",
                "famous_for": raw_desc[:150] + "..." if len(raw_desc) > 150 else raw_desc,
                "docent_details": raw_desc,
                "media": {"photo_url": "", "attribution": "Rajasthan Tourism Portal"},
                "trust_status": "government_verified",
                "synapses": [{"connection": "Extracted via automated parsing of state tourism directories."}]
            }
            
            # Avoid duplicate titles
            if not any(n['title'].lower() == clean_title.lower() for n in festival_nodes):
                festival_nodes.append(node)

    output_path = "tourism_raw_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(festival_nodes, f, indent=2, ensure_ascii=False)

    print(f"\nSuccess! Extracted {len(festival_nodes)} cleanly formatted festivals.")
    print(f"Data saved to {output_path}.")

except Exception as e:
    print(f"Scrape failed: {e}")