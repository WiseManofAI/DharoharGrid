import json
import os

cultural_nodes = [
    {
        "node_id": "IN-RJ-GAS-001",
        "title": "Dal Baati Churma",
        "category": "GASTRONOMY_HERITAGE",
        "coordinates": {"lat": 24.5854, "lng": 73.7125}, # Origin: Mewar / Udaipur
        "era": "8th Century (Mewar Kingdom)",
        "famous_for": "The quintessential Rajasthani survival food turned royal feast.",
        "nearby_culture": "Rajput battlefield logistics.",
        "docent_details": "Originating as a survival food for Mewar warriors. The 'baati' (hard wheat dough) was buried under hot desert sand to bake during the day while soldiers fought, then unearthed and eaten with locally available lentils.",
        "media": {"photo_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Dal_Baati_Churma.jpg", "attribution": "Wikimedia Commons"},
        "trust_status": "verified",
        "synapses": [{"connection": "Evolved from battlefield sustenance to a ceremonial royal feast."}]
    },
    {
        "node_id": "IN-RJ-GAS-002",
        "title": "Jodhpuri Pyaaz Kachori",
        "category": "GASTRONOMY_HERITAGE",
        "coordinates": {"lat": 26.2389, "lng": 73.0243}, # Origin: Jodhpur
        "era": "Early 20th Century",
        "famous_for": "A deep-fried pastry filled with spicy onion filling, originating in the Blue City.",
        "nearby_culture": "Marwari trading community snack culture.",
        "docent_details": "Invented in the street food stalls of Jodhpur. The arid climate made onions a staple crop, which were heavily spiced to prevent spoilage in the desert heat before being stuffed into a crisp Maida flour shell.",
        "media": {"photo_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Pyaaz_ki_Kachori.jpg", "attribution": "Wikimedia Commons"},
        "trust_status": "verified",
        "synapses": [{"connection": "A culinary staple that spread along Marwari trade routes across India."}]
    },
    {
        "node_id": "IN-RJ-GAS-003",
        "title": "Jaipuri Ghevar",
        "category": "GASTRONOMY_FESTIVAL",
        "coordinates": {"lat": 26.9124, "lng": 75.7873}, # Origin: Jaipur
        "era": "16th Century",
        "famous_for": "A disc-shaped honeycomb sweet soaked in syrup, tied to the Teej festival.",
        "nearby_culture": "Monsoon celebrations and royal confectionery.",
        "docent_details": "A complex dessert requiring precise moisture and temperature control, making it a monsoon specialty. It is traditionally gifted to newly married daughters during the Shraavana month.",
        "media": {"photo_url": "https://commons.wikimedia.org/wiki/Special:FilePath/GhevarRajasthaniSweet.jpg", "attribution": "Wikimedia Commons"},
        "trust_status": "verified",
        "synapses": [{"connection": "Reflects the highly refined sugar-craft of the Jaipur royal kitchens."}]
    },
    {
        "node_id": "IN-RJ-GAS-004",
        "title": "Laal Maas (Red Meat)",
        "category": "GASTRONOMY_HERITAGE",
        "coordinates": {"lat": 25.1388, "lng": 75.8362}, # Origin: Rajputana Hunting Camps
        "era": "10th Century",
        "famous_for": "A fiery Rajasthani mutton curry cooked with a paste of Mathania red chilies.",
        "nearby_culture": "Rajput royal hunting (Shikar) traditions.",
        "docent_details": "Historically prepared in hunting camps using wild game like boar or deer. The massive amount of garlic and fierce Mathania chilies were used to mask the gamy odor of wild meat.",
        "media": {"photo_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Laal-Maans.jpg", "attribution": "Wikimedia Commons"},
        "trust_status": "verified",
        "synapses": [{"connection": "A direct culinary artifact of Rajput martial and hunting culture."}]
    },
    {
        "node_id": "IN-RJ-INT-001",
        "title": "Jaipur Blue Pottery",
        "category": "INTANGIBLE_CRAFT",
        "coordinates": {"lat": 26.9200, "lng": 75.7800},
        "era": "19th Century",
        "famous_for": "A GI-tagged traditional craft using a dough of quartz stone powder instead of clay.",
        "nearby_culture": "Meenakari enamel work.",
        "docent_details": "Introduced by Sawai Ram Singh II. The vibrant blue color comes from cobalt oxide. It is fired at low temperatures, making it fragile but stunningly vibrant.",
        "media": {"photo_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Blue_pottery_of_Jaipur.jpg", "attribution": "Wikimedia Commons"},
        "trust_status": "verified",
        "synapses": [{"connection": "Shares material chemistry with glazed tilework found in Mughal monuments."}]
    },
    {
        "node_id": "IN-RJ-INT-002",
        "title": "Manganiyar Folk Music",
        "category": "INTANGIBLE_MUSIC",
        "coordinates": {"lat": 25.7500, "lng": 71.4167}, # Origin: Barmer Region
        "era": "Ancient Oral Tradition",
        "famous_for": "Soulful desert music performed by a hereditary community of musicians.",
        "nearby_culture": "Sindhi-Sufi syncretic poetry.",
        "docent_details": "The Manganiyars sing in a highly ornamented style using instruments like the Kamaicha. Their repertoire blends classical Hindustani ragas with folk rhythms.",
        "media": {"photo_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Manganiyar_Singers.jpg", "attribution": "Wikimedia Commons"},
        "trust_status": "verified",
        "synapses": [{"connection": "A musical cousin to the Langa community traditions of the Thar."}]
    },
    {
        "node_id": "IN-RJ-INT-003",
        "title": "Kalbelia Dance",
        "category": "INTANGIBLE_DANCE",
        "coordinates": {"lat": 26.4897, "lng": 74.5511}, # Origin: Pushkar / Ajmer
        "era": "Traditional Nomadic",
        "famous_for": "A fast-paced folk dance performed by the Kalbelia snake-charmer community.",
        "nearby_culture": "Nomadic desert survival traditions.",
        "docent_details": "Recognized by UNESCO. Dancers wear black skirts embroidered with silver ribbons that resemble serpent skin, moving to the hypnotic rhythm of the 'Poongi'.",
        "media": {"photo_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Kalbelia.jpg", "attribution": "Wikimedia Commons"},
        "trust_status": "verified",
        "synapses": [{"connection": "Linked to ancient animistic reverence of serpents."}]
    },
    {
        "node_id": "IN-RJ-INT-004",
        "title": "Pichwai Paintings",
        "category": "INTANGIBLE_CRAFT",
        "coordinates": {"lat": 24.9272, "lng": 73.8160}, # Origin: Nathdwara
        "era": "17th Century",
        "famous_for": "Intricate cloth paintings depicting the life of Lord Krishna.",
        "nearby_culture": "Pushtimarg Vaishnavite temple rituals.",
        "docent_details": "Created on starched cotton using natural colors derived from minerals, vegetables, and pure gold. It can take several months to complete one piece.",
        "media": {"photo_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Pichwai_by_unknown_Rajasthani_artist.jpg", "attribution": "Wikimedia Commons"},
        "trust_status": "verified",
        "synapses": [{"connection": "Shares stylistic elements with miniature paintings of the Mewar school."}]
    }
]

output_path = "rajasthan_master.json"

# Safely read existing data and strip out the old broken cultural nodes
if os.path.exists(output_path):
    with open(output_path, "r", encoding="utf-8") as f:
        master_nodes = json.load(f)
        # Remove old GAS/INT nodes so we don't get duplicates
        master_nodes = [n for n in master_nodes if not n["node_id"].startswith("IN-RJ-GAS") and not n["node_id"].startswith("IN-RJ-INT")]
else:
    master_nodes = []

# Inject the new high-quality nodes
master_nodes.extend(cultural_nodes)

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(master_nodes, f, indent=2, ensure_ascii=False)

print(f"Success! Injected {len(cultural_nodes)} premium Gastronomy & Intangible nodes.")
print("Refresh your browser to see the beautiful images and accurate origin locations!")