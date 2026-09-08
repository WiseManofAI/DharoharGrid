import json
import urllib.request
import urllib.parse
import time
import os

output_path = "rajasthan_master.json"

if not os.path.exists(output_path):
    print("Error: rajasthan_master.json not found!")
    exit()

with open(output_path, "r", encoding="utf-8") as f:
    nodes = json.load(f)

print(f"Scanning all {len(nodes)} nodes via Wikipedia API for real archival images...")

def fetch_wiki_thumb(title):
    query = f"{title} Rajasthan heritage architecture monument"
    url = "https://en.wikipedia.org/w/api.php?action=query&generator=search&gsrsearch=" + urllib.parse.quote(query) + "&gsrlimit=1&prop=pageimages&pithumbsize=600&format=json"
    req = urllib.request.Request(url, headers={'User-Agent': 'DharoharGrid-Hackathon/1.0'})
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
        pages = data.get('query', {}).get('pages', {})
        for page_id in pages:
            thumb = pages[page_id].get('thumbnail', {})
            if 'source' in thumb:
                return thumb['source']
    except:
        pass
    return ""

found_count = 0

for idx, node in enumerate(nodes):
    current_photo = node.get("media", {}).get("photo_url", "")
    
    # Only search if photo is currently empty
    if not current_photo:
        title = node.get("title", "")
        img_url = fetch_wiki_thumb(title)
        
        if img_url:
            if "media" not in node:
                node["media"] = {}
            node["media"]["photo_url"] = img_url
            node["media"]["attribution"] = "Wikipedia Commons API"
            found_count += 1
            print(f"[{idx+1}/{len(nodes)}] ✓ Found: {title}")
            
        time.sleep(0.3) # Be polite to Wikipedia's servers

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(nodes, f, indent=2, ensure_ascii=False)

print(f"\nSuccess! Automatically populated {found_count} real images across your dataset.")