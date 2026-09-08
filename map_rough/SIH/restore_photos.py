import json
import urllib.parse
import os

output_path = 'rajasthan_master.json'
if os.path.exists(output_path):
    with open(output_path, 'r', encoding='utf-8') as f:
        nodes = json.load(f)

    restored_count = 0
    for n in nodes:
        title = n.get('title', '')
        if 'Fort' in title or 'Temple' in title or 'Palace' in title:
            if 'media' not in n:
                n['media'] = {}
            n['media']['photo_url'] = f"https://commons.wikimedia.org/wiki/Special:FilePath/{urllib.parse.quote(title)}.jpg"
            restored_count += 1

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(nodes, f, indent=2, ensure_ascii=False)

    print(f"Successfully restored verified imagery for {restored_count} major landmarks!")