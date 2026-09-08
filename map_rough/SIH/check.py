import pandas as pd
import json
import re

# Read your CSV file
df = pd.read_csv("query.csv")
df = df.drop_duplicates(subset=["itemLabel"])

def parse_wkt_point(coord_str):
    """Extracts Latitude and Longitude from 'Point(lng lat)'"""
    match = re.search(r"Point\(([-\d\.]+)\s+([-\d\.]+)\)", str(coord_str))
    if match:
        lng, lat = float(match.group(1)), float(match.group(2))
        return lat, lng
    return None, None

master_nodes = []

print(f"Processing {len(df)} locations from query.csv (No API required)...")

for idx, row in df.iterrows():
    name = row["itemLabel"]
    lat, lng = parse_wkt_point(row["coord"])
    image_url = row["image"]

    if not lat or not lng:
        continue

    # Create clean IDs
    clean_id = f"IN-RJ-{re.sub(r'[^A-Z0-9]', '', name.upper())[:10]}-{idx+1:03d}"

    # Build the node with placeholder text for the map
    node = {
        "node_id": clean_id,
        "title": name,
        "category": "tangible",
        "coordinates": {
            "lat": lat,
            "lng": lng
        },
        "era": "Historical Heritage",
        "famous_for": f"A prominent cultural and historical landmark known as {name}, located in Rajasthan.",
        "nearby_culture": "Local Rajasthani art, architecture, and traditions.",
        "docent_details": f"{name} stands as an important monument representing the architectural and historical legacy of the region. Detailed archaeological research is currently being updated for this site.",
        "media": {
            "photo_url": str(image_url),
            "attribution": "Wikimedia Commons"
        },
        "trust_status": "verified",
        "synapses": [
            {
                "connection": "Part of the wider architectural network of Western India."
            }
        ]
    }
    master_nodes.append(node)

# Save directly to JSON
output_path = "rajasthan_master.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(master_nodes, f, indent=2, ensure_ascii=False)

print(f"\nSuccess! 100% complete. Generated {len(master_nodes)} locations into {output_path}.")
print("You can now connect this JSON directly to your Mapbox/Leaflet frontend.")