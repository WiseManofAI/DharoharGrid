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
    master_nodes = json.load(f)

print(f"Scanning {len(master_nodes)} nodes for missing photos...")

def get_wiki_image(search_query):
    query = f"{search_query} Rajasthan heritage"
    url = "https://en.wikipedia.org/w/api.php?action=query&generator=search&gsrsearch=" + urllib.parse.quote(query) + "&gsrlimit=1&prop=pageimages&pithumbsize=500&format=json"
    
    req = urllib.request.Request(url, headers={'User-Agent': 'DharoharGrid-Hackathon/1.0'})
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
        pages = data.get('query', {}).get('pages', {})
        for page_id in pages:
            thumbnail = pages[page_id].get('thumbnail', {})
            if 'source' in thumbnail:
                return thumbnail['source']
    except:
        pass
    return ""

updated_count = 0

for idx, node in enumerate(master_nodes):
    current_photo = node.get("media", {}).get("photo_url", "")
    
    if not current_photo or current_photo.startswith("https://commons.wikimedia.org/wiki/Special:FilePath/"):
        # If it's empty or using the old wiki file path link, let's look for a direct thumbnail
        image_url = get_wiki_image(node['title'])
        
        if image_url:
            if "media" not in node:
                node["media"] = {}
            node["media"]["photo_url"] = image_url
            node["media"]["attribution"] = "Wikipedia Commons (Auto-Fetched)"
            updated_count += 1
            print(f"  [{idx+1}/{len(master_nodes)}] ✓ Found image for: {node['title']}")
        else:
            print(f"  [{idx+1}/{len(master_nodes)}] ✗ No image found for: {node['title']}")
            
        time.sleep(0.4) # Be polite to Wikipedia servers

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(master_nodes, f, indent=2, ensure_ascii=False)

print(f"\nSuccess! Auto-populated {updated_count} images across your master dataset.")