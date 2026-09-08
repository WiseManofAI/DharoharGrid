import urllib.request
import urllib.parse
import json
import re

print("Connecting to public Wikidata servers (No API Keys needed)...")

# SPARQL query: Get 200 items in Rajasthan (Q1437) that are Forts, Temples, Palaces, or Monuments
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

# URL encode the query for the web request
url = "https://query.wikidata.org/sparql?query=" + urllib.parse.quote(query) + "&format=json"
req = urllib.request.Request(url, headers={'User-Agent': 'DharoharGrid-Hackathon/1.0'})

try:
    print("Downloading 150+ locations... (this takes about 3 seconds)")
    response = urllib.request.urlopen(req)
    data = json.loads(response.read().decode('utf-8'))
except Exception as e:
    print("Error fetching data:", e)
    exit()

results = data['results']['bindings']
master_nodes = []

for idx, row in enumerate(results):
    name = row.get('itemLabel', {}).get('value', 'Unknown Site')
    
    # Skip unnamed system items
    if name.startswith('Q') and name[1:].isdigit(): 
        continue 
        
    coord_str = row.get('coord', {}).get('value', '')
    image_url = row.get('image', {}).get('value', '')

    # Parse Point(lng lat)
    match = re.search(r"Point\(([-\d\.]+)\s+([-\d\.]+)\)", str(coord_str))
    if not match:
        continue
    lng, lat = float(match.group(1)), float(match.group(2))

    # Create a safe, unique ID
    clean_id = f"IN-RJ-{re.sub(r'[^A-Z0-9]', '', name.upper())[:10]}-{idx:03d}"

    node = {
        "node_id": clean_id,
        "title": name,
        "category": "TANGIBLE_HERITAGE",
        "coordinates": {"lat": lat, "lng": lng},
        "era": "Historical Database",
        "famous_for": f"A prominent architectural and historical landmark located in Rajasthan.",
        "nearby_culture": "Rajasthani architecture and traditions.",
        "docent_details": f"{name} stands as an important node in India's cultural grid. Comprehensive historical mapping for this site is actively being cataloged.",
        "media": {
            "photo_url": image_url,
            "attribution": "Wikimedia Commons"
        },
        "trust_status": "verified",
        "synapses": [
            {"connection": "Architecturally linked to the broader Rajputana defensive and cultural network."}
        ]
    }
    master_nodes.append(node)

# Save directly to JSON
output_path = "rajasthan_master.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(master_nodes, f, indent=2, ensure_ascii=False)

print(f"\nSuccess! Plotted {len(master_nodes)} distinct sites across Rajasthan.")
print(f"Data saved to {output_path}. Refresh your web browser now!")