import urllib.request
import urllib.parse
import json
import os

print("Connecting to OpenStreetMap (Overpass API) to find local hidden heritage...")

# Overpass QL Query: Find all named historical sites in Rajasthan
overpass_query = """
[out:json][timeout:90];
area["name"="Rajasthan"]["admin_level"="4"]->.searchArea;
(
  node["historic"]["name"](area.searchArea);
  way["historic"]["name"](area.searchArea);
  relation["historic"]["name"](area.searchArea);
);
out center;
"""

url = "https://overpass-api.de/api/interpreter"
data = urllib.parse.urlencode({'data': overpass_query}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'User-Agent': 'DharoharGrid-Hackathon/1.0'})

try:
    print("Downloading hundreds of local stepwells, ruins, and forts... (takes about 5-10 seconds)")
    response = urllib.request.urlopen(req)
    osm_data = json.loads(response.read().decode('utf-8'))
except Exception as e:
    print("Error fetching OpenStreetMap data:", e)
    exit()

elements = osm_data.get('elements', [])
print(f"Found {len(elements)} raw historical locations!")

# Load existing data so we don't overwrite
output_path = "rajasthan_master.json"
master_nodes = []
seen_titles = set()

if os.path.exists(output_path):
    with open(output_path, "r", encoding="utf-8") as f:
        master_nodes = json.load(f)
        for node in master_nodes:
            seen_titles.add(node["title"].lower())

added_osm = 0

for idx, el in enumerate(elements):
    tags = el.get("tags", {})
    name = tags.get("name", "").strip()
    
    if not name or name.lower() in seen_titles:
        continue
        
    historic_type = tags.get("historic", "heritage site").capitalize()
    
    # Get coordinates (center for ways/relations)
    lat = el.get("lat") or el.get("center", {}).get("lat")
    lng = el.get("lon") or el.get("center", {}).get("lon")
    
    if not lat or not lng:
        continue
        
    clean_id = f"IN-RJ-OSM-{idx:04d}"
    
    node = {
        "node_id": clean_id,
        "title": name,
        "category": f"TANGIBLE_{historic_type.upper()}",
        "coordinates": {"lat": lat, "lng": lng},
        "era": "Local Heritage",
        "famous_for": f"A local {historic_type.lower()} documented by open-source ground mapping.",
        "nearby_culture": "Deep regional heritage.",
        "docent_details": f"This {historic_type.lower()} represents the grassroots cultural infrastructure of Rajasthan.",
        "media": {"photo_url": "", "attribution": "OpenStreetMap Contributors"},
        "trust_status": "community_verified",
        "synapses": [{"connection": "Part of the local micro-heritage network."}]
    }
    
    master_nodes.append(node)
    seen_titles.add(name.lower())
    added_osm += 1

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(master_nodes, f, indent=2, ensure_ascii=False)

print(f"\nSuccess! Added {added_osm} NEW hyper-local sites from OpenStreetMap.")
print(f"Your map now has {len(master_nodes)} TOTAL nodes! Refresh your browser.")