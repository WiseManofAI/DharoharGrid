import pandas as pd
import json
import ssl

# Bypass SSL verification for government portals with expired certificates
ssl._create_default_https_context = ssl._create_unverified_context

print("Connecting to Archaeological Survey of India (ASI) Jaipur Circle...")
url = "https://asijaipurcircle.in/Monuments.aspx"

print("Connecting to Archaeological Survey of India (ASI) Jaipur Circle...")
url = "https://asijaipurcircle.in/Monuments.aspx"

try:
    print("Scraping official government monument tables...")
    
    # Pandas automatically finds the <table> tags on the webpage
    tables = pd.read_html(url)
    
    # The first table contains the monument list
    asi_df = tables[0]
    
    print(f"Success! Found {len(asi_df)} central protected monuments.")
    
    # Clean the column names just in case of hidden spaces
    asi_df.columns = asi_df.columns.str.strip()
    
    asi_nodes = []
    
    for idx, row in asi_df.iterrows():
        name = str(row.get("Name of the Monument / Site", "")).strip()
        locality = str(row.get("Locality", "")).strip()
        district = str(row.get("District", "")).strip()
        
        if not name or name == "nan":
            continue
            
        clean_id = f"IN-RJ-ASI-{idx:03d}"
        
        node = {
            "node_id": clean_id,
            "title": name,
            "category": "TANGIBLE_ASI_PROTECTED",
            "location_text": f"{locality}, {district}",
            "era": "Government Protected Antiquity",
            "famous_for": f"A centrally protected monument located in the {district} district.",
            "nearby_culture": f"Regional heritage of {district}.",
            "docent_details": f"Officially gazetted by the Archaeological Survey of India (ASI) Jaipur Circle. Locality: {locality}.",
            "media": {"photo_url": "", "attribution": "ASI Jaipur Circle"},
            "trust_status": "government_verified",
            "synapses": [{"connection": "Included in the Central Protected Monuments national registry."}]
        }
        asi_nodes.append(node)
        
    # Save to a separate JSON file so we can look at it
    output_path = "asi_raw_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(asi_nodes, f, indent=2, ensure_ascii=False)
        
    print(f"Saved {len(asi_nodes)} raw ASI records to {output_path}!")
    print("You can click on 'asi_raw_data.json' in your left sidebar to see the extracted government data.")
    
except Exception as e:
    print(f"Error extracting ASI data: {e}")