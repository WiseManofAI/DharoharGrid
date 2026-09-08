import json
import os

print("Injecting clean, professionally formatted Fairs & Festivals...")

festival_nodes = [
    {
        "node_id": "IN-RJ-FEST-001",
        "title": "Desert Festival",
        "category": "INTANGIBLE_FESTIVAL",
        "coordinates": {"lat": 26.9157, "lng": 70.9083},
        "location_text": "Jaisalmer",
        "era": "Annual Cultural Event",
        "famous_for": "A globally renowned celebration of Thar Desert culture featuring camel races and Kalbelia dances.",
        "docent_details": "Once a year, the empty sands around Jaisalmer come alive with a mesmerising performance on the sand dunes in the form of the Desert Festival, organised by the Department of Tourism around January-February.",
        "media": {"photo_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Desert_festival_jaisalmer.jpg", "attribution": "Rajasthan Tourism Calendar"},
        "trust_status": "government_verified",
        "synapses": [{"connection": "Central node for celebrating Thar regional folklore."}]
    },
    {
        "node_id": "IN-RJ-FEST-002",
        "title": "Pushkar Camel Fair",
        "category": "INTANGIBLE_FESTIVAL",
        "coordinates": {"lat": 26.4897, "lng": 74.5511},
        "location_text": "Pushkar, Ajmer",
        "era": "Ancient Trade & Religious Gathering",
        "famous_for": "One of the world's largest traditional camel and livestock fairs.",
        "docent_details": "Occurs annually in November. Combines camel trading, religious bathing in Pushkar Lake, and massive cultural performances.",
        "media": {"photo_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Pushkar_camel_fair.jpg", "attribution": "Rajasthan Tourism Calendar"},
        "trust_status": "government_verified",
        "synapses": [{"connection": "A massive economic and cultural convergence point."}]
    },
    {
        "node_id": "IN-RJ-FEST-003",
        "title": "Teej Festival",
        "category": "INTANGIBLE_FESTIVAL",
        "coordinates": {"lat": 26.9220, "lng": 75.8200},
        "location_text": "Jaipur",
        "era": "Traditional Monsoon Festival",
        "famous_for": "A vibrant monsoon celebration dedicated to Goddess Parvati, featuring grand processions.",
        "docent_details": "Observed in July/August. The royal procession of the Goddess passes through the Old City. Women dress in green and celebrate the arrival of rain.",
        "media": {"photo_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Teej_Procession_Jaipur.jpg", "attribution": "Rajasthan Tourism Calendar"},
        "trust_status": "government_verified",
        "synapses": [{"connection": "Deeply linked to the seasonal agrarian cycle."}]
    },
    {
        "node_id": "IN-RJ-FEST-004",
        "title": "Mewar Festival",
        "category": "INTANGIBLE_FESTIVAL",
        "coordinates": {"lat": 24.5712, "lng": 73.6915},
        "location_text": "Udaipur",
        "era": "Traditional Spring Festival",
        "famous_for": "A celebration of spring culminating in a spectacular boat procession on Lake Pichola.",
        "docent_details": "Held in March/April. Women dress the idols of Isar and Gauri and carry them to the Gangaur Ghat to be placed on royal boats.",
        "media": {"photo_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Gangaur_ghat_udaipur.jpg", "attribution": "Rajasthan Tourism Calendar"},
        "trust_status": "government_verified",
        "synapses": [{"connection": "Showcases the integration of religious ritual with Udaipur's aquatic geography."}]
    },
    {
        "node_id": "IN-RJ-FEST-005",
        "title": "Bikaner Camel Festival",
        "category": "INTANGIBLE_FESTIVAL",
        "coordinates": {"lat": 28.0229, "lng": 73.3119},
        "location_text": "Bikaner",
        "era": "Annual Cultural Event",
        "famous_for": "Honors the camel as the 'Ship of the Desert' with fur-shearing art and races.",
        "docent_details": "Organized every January by the Department of Tourism. Celebrates the deep historical reliance on camels in the harsh desert economy.",
        "media": {"photo_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Bikaner_Camel_Festival.jpg", "attribution": "Rajasthan Tourism Calendar"},
        "trust_status": "government_verified",
        "synapses": [{"connection": "Highlights human-animal symbiosis in arid climates."}]
    },
    {
        "node_id": "IN-RJ-FEST-006",
        "title": "Baneshwar Fair",
        "category": "INTANGIBLE_FESTIVAL",
        "coordinates": {"lat": 23.8058, "lng": 74.0205},
        "location_text": "Dungarpur",
        "era": "Traditional Tribal Gathering",
        "famous_for": "A massive tribal festival of the Bhil community held at a river delta.",
        "docent_details": "Held in January/February at the confluence of the Mahi and Som rivers. It is the largest tribal fair in Rajasthan.",
        "media": {"photo_url": "", "attribution": "Rajasthan Tourism Calendar"},
        "trust_status": "government_verified",
        "synapses": [{"connection": "The most significant indigenous/tribal node on the cultural map."}]
    },
    {
        "node_id": "IN-RJ-FEST-007",
        "title": "Marwar Festival",
        "category": "INTANGIBLE_FESTIVAL",
        "coordinates": {"lat": 26.2389, "lng": 73.0243},
        "location_text": "Jodhpur",
        "era": "Historical Commemoration",
        "famous_for": "Celebrated to commemorate the valor and bravery of Rajput warriors.",
        "docent_details": "Held annually in September/October. Folk artists perform traditional ballads of Rajput heroes, keeping martial history alive.",
        "media": {"photo_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Marwar_festival.jpg", "attribution": "Rajasthan Tourism Calendar"},
        "trust_status": "government_verified",
        "synapses": [{"connection": "Oral preservation of regional military history."}]
    },
    {
        "node_id": "IN-RJ-FEST-008",
        "title": "Urs Festival",
        "category": "INTANGIBLE_FESTIVAL",
        "coordinates": {"lat": 26.4560, "lng": 74.6270},
        "location_text": "Ajmer Sharif Dargah",
        "era": "Sufi Commemoration",
        "famous_for": "A massive Sufi festival symbolizing peace, devotion, and communal harmony.",
        "docent_details": "Commemorates the death anniversary of Sufi saint Khwaja Moinuddin Chishti with hypnotic Qawwali music.",
        "media": {"photo_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Ajmer_Sharif_Dargah.jpg", "attribution": "Rajasthan Tourism Calendar"},
        "trust_status": "government_verified",
        "synapses": [{"connection": "The primary hub of Sufi syncretic traditions in Western India."}]
    },
    {
        "node_id": "IN-RJ-FEST-009",
        "title": "Kumbhalgarh Festival",
        "category": "INTANGIBLE_FESTIVAL",
        "coordinates": {"lat": 25.1485, "lng": 73.5822},
        "location_text": "Rajsamand",
        "era": "Annual Cultural Event",
        "famous_for": "A vibrant classical dance and music showcase set against Kumbhalgarh Fort.",
        "docent_details": "Organized in December by the Tourism Department, combining massive tangible architecture with intangible classical arts.",
        "media": {"photo_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Kumbhalgarh_Fort.jpg", "attribution": "Rajasthan Tourism Calendar"},
        "trust_status": "government_verified",
        "synapses": [{"connection": "Intersection of tangible architecture and intangible performance art."}]
    },
    {
        "node_id": "IN-RJ-FEST-010",
        "title": "Elephant Festival",
        "category": "INTANGIBLE_FESTIVAL",
        "coordinates": {"lat": 26.9124, "lng": 75.7873},
        "location_text": "Jaipur",
        "era": "Traditional Royal Pageantry",
        "famous_for": "Showcases beautifully painted elephants in grand parades.",
        "docent_details": "Usually held around Holi in March, highlighting Rajasthan's royal heritage.",
        "media": {"photo_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Elephant_Festival_Jaipur.jpg", "attribution": "Rajasthan Tourism Calendar"},
        "trust_status": "government_verified",
        "synapses": [{"connection": "Reflects the historical pageantry of the Jaipur royal court."}]
    }
]

output_path = "rajasthan_master.json"

if os.path.exists(output_path):
    with open(output_path, "r", encoding="utf-8") as f:
        master_nodes = json.load(f)
        master_nodes = [n for n in master_nodes if not n["node_id"].startswith("IN-RJ-FEST")]
else:
    master_nodes = []

master_nodes.extend(festival_nodes)

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(master_nodes, f, indent=2, ensure_ascii=False)

print(f"Success! Cleaned and injected {len(festival_nodes)} festivals.")
print("Refresh your browser map!")