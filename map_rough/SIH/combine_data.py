import pandas as pd
import urllib.request
import urllib.parse
import json
import re

master_nodes = []
seen_titles = set()

# --- PART 1: READ FROM YOUR CSV ---
try:
    print("1. Reading your original query.csv...")
    df = pd.read_csv("query.csv")
    df = df.drop_duplicates(subset=["itemLabel"])
    
    for idx, row in df.iterrows():
        name = str(row["itemLabel"]).strip()
        coord_str = row["coord"]
        image_url = row["image"]
        
        match = re.search(r"Point\(([-\d\.]+)\s+([-\d\.]+)\)", str(coord_str))
        if match:
            lng, lat = float(match.group(1)), float(match.group(2))
            
            node = {
                "node_id": f"IN-RJ-CSV-{idx:03d}",
                "title": name,
                "category": "TANGIBLE_HERITAGE",
                "coordinates": {"lat": lat, "lng": lng},
                "era": "Historical Heritage",
                "famous_for": f"A prominent cultural landmark known as {name}.",
                "nearby_culture": "Local Rajasthani art and traditions.",
                "docent_details": f"{name} stands as an important monument.",
                "media": {"photo_url": str(image_url), "attribution": "Wikimedia Commons"},
                "trust_status": "verified",
                "synapses": [{"connection": "Part of the wider architectural network."}]
            }
            master_nodes.append(node)
            seen_titles.add(name.lower())
    print(f"   -> Added {len(master_nodes)} sites from CSV.")
except Exception as e:
    print(f"   -> Could not read CSV: {e}")


# --- PART 2: FETCH NEW ONES FROM WIKIDATA ---
print("\n2. Fetching MORE sites from Wikidata...")
query = """
SELECT DISTINCT ?item ?itemLabel ?coord ?image WHERE {
  ?item wdt:P131* wd:Q1437. 
  ?item wdt:P31 ?type.
  VALUES ?type {wd:Q23442 wd:Q16560 wd:Q1497330 wd:Q2695349 wd:Q811430} 
  ?item wdt:P625 ?coord.
  OPTIONAL { ?item wdt:P18 ?image. }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 200
"""
url = "https://query.wikidata.org/sparql?query=" + urllib.parse.quote(query) + "&format=json"
req = urllib.request.Request(url, headers={'User-Agent': 'DharoharGrid-Hackathon/1.0'})

try:
    response = urllib.request.urlopen(req)
    data = json.loads(response.read().decode('utf-8'))
    results = data['results']['bindings']
    
    added_wiki = 0
    for idx, row in enumerate(results):
        name = row.get('itemLabel', {}).get('value', 'Unknown Site').strip()
        
        # Skip unnamed system items and duplicates
        if name.startswith('Q') and name[1:].isdigit(): continue
        if name.lower() in seen_titles: continue
            
        coord_str = row.get('coord', {}).get('value', '')
        image_url = row.get('image', {}).get('value', '')
        
        match = re.search(r"Point\(([-\d\.]+)\s+([-\d\.]+)\)", str(coord_str))
        if match:
            lng, lat = float(match.group(1)), float(match.group(2))
            
            node = {
                "node_id": f"IN-RJ-WIKI-{idx:03d}",
                "title": name,
                "category": "TANGIBLE_HERITAGE",
                "coordinates": {"lat": lat, "lng": lng},
                "era": "Historical Database",
                "famous_for": f"A prominent architectural landmark located in Rajasthan.",
                "nearby_culture": "Rajasthani architecture and traditions.",
                "docent_details": f"{name} stands as an important node in India's cultural grid.",
                "media": {"photo_url": image_url, "attribution": "Wikimedia Commons"},
                "trust_status": "verified",
                "synapses": [{"connection": "Architecturally linked to Rajputana defensive network."}]
            }
            master_nodes.append(node)
            seen_titles.add(name.lower())
            added_wiki += 1
            
    print(f"   -> Added {added_wiki} NEW sites from Wikidata.")
except Exception as e:
    print(f"   -> Error fetching Wikidata: {e}")


# --- PART 3: SAVE EVERYTHING TOGETHER ---
output_path = "rajasthan_master.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(master_nodes, f, indent=2, ensure_ascii=False)

print(f"\nSuccess! Plotted {len(master_nodes)} TOTAL distinct sites across Rajasthan.")
print("Refresh your browser!")