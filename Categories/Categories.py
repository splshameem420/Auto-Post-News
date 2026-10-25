import json
import os

import requests


def load_categories_config(file_path="categories.json"):
    if not os.path.exists(file_path):
        print(f"⚠️ Warning: {file_path} file not found!")
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ Error loading JSON config: {e}")
        return []

def get_or_create_category(wp_site_url, auth, headers, cat_input):
    try:
        if isinstance(cat_input, int) or (isinstance(cat_input, str) and cat_input.isdigit()):
            return int(cat_input)
            
        cat_name = str(cat_input).strip()
        res = requests.get(f"{wp_site_url}/wp-json/wp/v2/categories?search={cat_name}", auth=auth, headers=headers, timeout=15)
        if res.status_code == 200:
            cats = res.json()
            for cat in cats:
                if cat['name'].lower() == cat_name.lower():
                    return cat['id']
                
        create_res = requests.post(f"{wp_site_url}/wp-json/wp/v2/categories", json={'name': cat_name}, auth=auth, headers=headers, timeout=15)
        if create_res.status_code == 201:
            return create_res.json()['id']
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ Category Processing Fail ({cat_input}): {e}")
    return None

def get_category_from_text(text, config):
    if not text:
        return None
        
    text_lower = str(text).lower()
    
    for cat in config:
        cat_name = cat.get("Category Name", "").lower()
        if cat_name and (cat_name in text_lower or text_lower in cat_name):
            return cat["ID"]
            
        filters = cat.get("Filter", [])
        for filter_str in filters:
            keywords = [kw.strip().lower() for kw in filter_str.split(",") if kw.strip()]
            for keyword in keywords:
                if keyword in text_lower:
                    return cat["ID"]
                    
    return None

def get_final_category_id(wp_site_url, auth, headers, scraped_category, title):
    config = load_categories_config("categories.json")
    
    selected_cat = None

    if scraped_category and str(scraped_category).strip():
        print(f"🔍 Checking Scraped Category: '{scraped_category}'")
        matched_id = get_category_from_text(scraped_category, config)
        if matched_id:
            print(f"✅ Filter 1 Matched! Category ID -> {matched_id}")
            selected_cat = matched_id
        else:
            print("⚠️ Scraped category did not match any JSON filter. Trying title filter...")

    if not selected_cat and title:
        print(f"🔍 Checking Title Filter for: '{title}'")
        matched_id_from_title = get_category_from_text(title, config)
        if matched_id_from_title:
            print(f"✅ Filter 2 Matched from Title! Category ID -> {matched_id_from_title}")
            selected_cat = matched_id_from_title

    if not selected_cat:
        selected_cat = scraped_category if scraped_category else "News"

    final_cat_id = get_or_create_category(wp_site_url, auth, headers, selected_cat)
    return final_cat_id