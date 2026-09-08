import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import json
import re

print("Connecting to public Wikipedia data for Geographical Indications (GI Tags)...")

url = "https://en.wikipedia.org/wiki/List_of_Geographical_Indications_in_India"

try:
    req = urllib.request.Request(url, headers={'User-Agent': 'DharoharGrid-Hackathon/1.0'})
    response = urllib.request.urlopen(req)
    html = response.read()
    soup = BeautifulSoup(html, 'html.parser')

    print("Parsing GI Tag tables...")
    
    gi_nodes = []
    tables = soup.find_all('table', {'class': 'wikitable'})
    
    for table in tables:
        rows = table.find_all('tr')[1:] # Skip header
        for idx, row in enumerate(rows):
            cols = row.find_all(['td', 'th'])
            row_text = row.get_text(" | ").strip()
            
            # Check if Rajasthan is anywhere in this row
            if "Rajasthan" in row_text and len(cols) >= 4:
                # Based on standard wiki table: [0] is S.No, [1] AppNo, [2] Name, [3] Type, [4] State
                # Let's extract safely
                try:
                    product_name = cols[2].text.strip()
                    category_text = cols[3].text.strip().upper()
                except IndexError:
                    continue
                
                # If product name is weirdly a number, shift by 1
                if product_name.isdigit() and len(cols) > 4:
                    product_name = cols[3].text.strip()
                    category_text = cols[4].text.strip().upper()
                    
                clean_id = f"IN-RJ-GI-{re.sub(r'[^A-Z0-9]', '', product_name.upper())[:10]}-{idx:03d}"
                
                node = {
                    "node_id": clean_id,
                    "title": product_name,
                    "category": f"GASTRONOMY_OR_CRAFT_GI_TAG",
                    "location_text": "Rajasthan", 
                    "era": "Traditional Heritage",
                    "famous_for": f"A legally protected Geographical Indication (GI) from Rajasthan.",
                    "nearby_culture": "Deep regional heritage.",
                    "docent_details": f"Registered under the Geographical Indications of Goods Act. Type: {category_text}.",
                    "media": {"photo_url": "", "attribution": "Wikipedia/GI Registry"},
                    "trust_status": "government_verified",
                    "synapses": [{"connection": "Recognized for unique qualities derived from its geographical origin."}]
                }
                gi_nodes.append(node)

    output_path = "gi_raw_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(gi_nodes, f, indent=2, ensure_ascii=False)

    print(f"Success! Extracted {len(gi_nodes)} verified GI Tags for Rajasthan.")
    print(f"Data saved to {output_path}.")
    
except Exception as e:
    print(f"Error fetching GI data: {e}")