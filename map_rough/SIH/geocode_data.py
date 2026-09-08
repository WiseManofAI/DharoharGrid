import json
import urllib.request
import urllib.parse
import time
import os

def geocode_location(location_name):
    """Uses the free OpenStreetMap Nominatim API to get coordinates"""
    # Adding 'Rajasthan, India' helps the search engine find the exact pin
    query = f"{location_name}, Rajasthan, India"
    url = "https://nominatim.openstreetmap.org/search?q=" + urllib.parse.quote(query) + "&format=json&limit=1"
    
    req = urllib.request.Request(url, headers={'User-Agent': 'DharoharGrid-Hackathon/1.0'})
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
        if len(data) > 0:
            return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        pass
    return None, None

def process_file(filename):
    if not os.path.exists(filename):
        return []
        
    with open(filename, "r", encoding="utf-8") as f:
        nodes = json.load(f)
        
    print(f"Finding GPS coordinates for {len(nodes)} items in {filename}...")
    
    valid_nodes = []
    for idx, node in enumerate(nodes):
        # 1. Try finding the exact monument/product name first
        lat, lng = geocode_location(node['title'])
        
        # 2. If it fails, zoom out and search by its District/City instead
        if not lat and 'location_text' in node:
            lat, lng = geocode_location(node['location_text'])
            
        if lat and lng:
            node['coordinates'] = {"lat": lat, "lng": lng}
            valid_nodes.append(node)
            print(f"  [{idx+1}/{len(nodes)}] ✓ Found: {node['title']}")
        else:
            print(f"  [{idx+1}/{len(nodes)}] ✗ Could not locate: {node['title']}")
            
        # STRICT RULE: We must sleep for 1 second between searches so the free server doesn't block us
        time.sleep(1.1)
        
    return valid_nodes

# 1. Find coordinates for the raw data
asi_geocoded = process_file("asi_raw_data.json")
gi_geocoded = process_file("gi_raw_data.json")

all_new_nodes = asi_geocoded + gi_geocoded

# 2. Merge them into your master map file
output_path = "rajasthan_master.json"
if os.path.exists(output_path):
    with open(output_path, "r", encoding="utf-8") as f:
        master_nodes = json.load(f)
else:
    master_nodes = []

master_nodes.extend(all_new_nodes)

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(master_nodes, f, indent=2, ensure_ascii=False)

print(f"\nSuccess! Plotted {len(all_new_nodes)} official ASI & GI nodes onto the map.")
print("Refresh your browser to see the new government-verified dots!")