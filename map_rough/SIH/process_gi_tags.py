import json
import os

print("Mapping 21 GI Tags to their exact geographical origins...")

# A hand-curated coordinate dictionary mapping the GI products to their specific towns
gi_origin_map = {
    "BIKANER": {"lat": 28.0229, "lng": 73.3119, "city": "Bikaner"},
    "JAIPUR": {"lat": 26.9124, "lng": 75.7873, "city": "Jaipur"},
    "KOTA": {"lat": 25.1814, "lng": 75.8322, "city": "Kota"},
    "MOLELA": {"lat": 24.9575, "lng": 73.7431, "city": "Molela, Rajsamand"},
    "SANGANER": {"lat": 26.8207, "lng": 75.7882, "city": "Sanganer"},
    "BAGRU": {"lat": 26.8166, "lng": 75.5458, "city": "Bagru"},
    "THEWA": {"lat": 24.0305, "lng": 74.7818, "city": "Pratapgarh"},
    "SOJAT": {"lat": 25.9229, "lng": 73.6669, "city": "Sojat, Pali"},
    "MAKRANA": {"lat": 27.0375, "lng": 74.7262, "city": "Makrana, Nagaur"},
    "POKARAN": {"lat": 26.9192, "lng": 71.9168, "city": "Pokhran, Jaisalmer"},
    "UDAIPUR": {"lat": 24.5854, "lng": 73.7125, "city": "Udaipur"},
    "JODHPUR": {"lat": 26.2389, "lng": 73.0243, "city": "Jodhpur"},
    "NATHDWARA": {"lat": 24.9272, "lng": 73.8160, "city": "Nathdwara"},
    "PICHHWAI": {"lat": 24.9272, "lng": 73.8160, "city": "Nathdwara"},
    "KATHPUTLI": {"lat": 26.2389, "lng": 73.0243, "city": "Marwar Region"}
}

# 1. Read the raw GI tags we scraped from Wikipedia
try:
    with open("gi_raw_data.json", "r", encoding="utf-8") as f:
        gi_nodes = json.load(f)
except FileNotFoundError:
    print("Error: gi_raw_data.json not found!")
    exit()

valid_gi_nodes = []

# 2. Assign exact coordinates based on the name
for node in gi_nodes:
    title_upper = node["title"].upper()
    found_origin = False
    
    for key, location_data in gi_origin_map.items():
        if key in title_upper:
            node["coordinates"] = {"lat": location_data["lat"], "lng": location_data["lng"]}
            node["location_text"] = location_data["city"]
            node["docent_details"] += f" Officially originates from {location_data['city']}."
            valid_gi_nodes.append(node)
            found_origin = True
            print(f" ✓ Mapped '{node['title']}' strictly to {location_data['city']}")
            break # Stop searching once we find a match
            
    # Default fallback for statewide items like "Phulkari"
    if not found_origin:
        node["coordinates"] = {"lat": 26.58, "lng": 73.84} # General Rajasthan center
        node["location_text"] = "Rajasthan (Statewide)"
        valid_gi_nodes.append(node)
        print(f" ⚠ Plotted '{node['title']}' to general state coordinates.")

# 3. Inject them into the main map dataset
output_path = "rajasthan_master.json"
if os.path.exists(output_path):
    with open(output_path, "r", encoding="utf-8") as f:
        master_nodes = json.load(f)
else:
    master_nodes = []

# Remove any old GI tags to avoid duplicates, then add the newly mapped ones
master_nodes = [n for n in master_nodes if "GI_TAG" not in n.get("category", "")]
master_nodes.extend(valid_gi_nodes)

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(master_nodes, f, indent=2, ensure_ascii=False)

print(f"\nSuccess! Injected {len(valid_gi_nodes)} perfectly plotted GI Tags into the map.")
print("Refresh your browser to see the new nodes!")