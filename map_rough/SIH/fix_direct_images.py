import json
import os

output_path = "rajasthan_master.json"
if os.path.exists(output_path):
    with open(output_path, "r", encoding="utf-8") as f:
        nodes = json.load(f)

    # 100% reliable direct photo links
    safe_photos = {
        "TANGIBLE": "https://images.unsplash.com/photo-1599661559890-50d4eb0c1b48?auto=format&fit=crop&q=80&w=600",
        "ASI": "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&q=80&w=600",
        "GI_TAG": "https://images.unsplash.com/photo-1609137144813-752467b52582?auto=format&fit=crop&q=80&w=600",
        "GASTRONOMY": "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?auto=format&fit=crop&q=80&w=600",
        "INTANGIBLE": "https://images.unsplash.com/photo-1605648916361-9bc12ad6a563?auto=format&fit=crop&q=80&w=600",
        "DEFAULT": "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=600"
    }

    for node in nodes:
        cat = node.get("category", "").upper()
        if "ASI" in cat:
            url = safe_photos["ASI"]
        elif "GI_TAG" in cat:
            url = safe_photos["GI_TAG"]
        elif "GASTRONOMY" in cat:
            url = safe_photos["GASTRONOMY"]
        elif "INTANGIBLE" in cat or "FESTIVAL" in cat:
            url = safe_photos["INTANGIBLE"]
        elif "TANGIBLE" in cat:
            url = safe_photos["TANGIBLE"]
        else:
            url = safe_photos["DEFAULT"]
            
        if "media" not in node:
            node["media"] = {}
        node["media"]["photo_url"] = url

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(nodes, f, indent=2, ensure_ascii=False)

    print("Success! Swapped all image URLs to ultra-reliable direct links.")