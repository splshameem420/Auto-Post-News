import copy
import html
import json
import os
from urllib.parse import urlparse

import requests
from slugify import slugify

CATEGORIES_FILE = "Categories.json"
DEFAULT_CATEGORY = "General"


# Load Json
def load_json_file(file_path):
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ Error loading {file_path}: {e}")
        return []


# Save Json
def save_json_file(file_path, data):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ Error saving {file_path}: {e}")


# Main Category Name List
def get_main_category_names():
    config = load_json_file(CATEGORIES_FILE)
    return [
        str(c.get("Category Name", "")).strip()
        for c in config
        if str(c.get("Category Name", "")).strip()
    ]


# Api
def _api(wp_site_url):
    return wp_site_url.rstrip("/") + "/wp-json/wp/v2"


# Value
def _valid_id(value):
    return value not in (None, "", "xx")


# Value Defain
def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


# Site Loder
def _same(a, b):
    return str(a or "").strip().casefold() == str(b or "").strip().casefold()


# Site Categories
def _reset_ids(data):
    for entry in data:
        if "ID" in entry:
            entry["ID"] = "xx"
        for sub in entry.get("Sub Categories", []):
            sub["ID"] = "xx"
    return data


# Load Site Categories With Loder
def load_site_categories(wp_site_url):
    stem, ext = os.path.splitext(CATEGORIES_FILE)
    site_file = f"{stem}_{_site_key(wp_site_url)}{ext}"
    if os.path.exists(site_file):
        return load_json_file(site_file), site_file
    return _reset_ids(copy.deepcopy(load_json_file(CATEGORIES_FILE))), site_file


# Return Or Crete Categories In Wp
def get_or_create_wp_category(wp_site_url, auth, headers, cat_name, parent_id=0):
    try:
        cat_name = str(cat_name).strip().upper()
        slug = slugify(cat_name) or None
        base = f"{_api(wp_site_url)}/categories"

        if slug:
            res = requests.get(
                base,
                params={"slug": slug, "parent": parent_id},
                auth=auth,
                headers=headers,
                timeout=15,
            )
            if res.status_code == 200 and res.json():
                return res.json()[0]["id"]

        res = requests.get(
            base,
            params={"search": cat_name, "parent": parent_id, "per_page": 100},
            auth=auth,
            headers=headers,
            timeout=15,
        )
        if res.status_code == 200:
            for cat in res.json():
                if (
                    html.unescape(cat.get("name", "")).strip().casefold()
                    == cat_name.casefold()
                ):
                    return cat["id"]

        payload = {"name": cat_name, "parent": parent_id}
        if slug:
            payload["slug"] = slug
        create_res = requests.post(
            base, json=payload, auth=auth, headers=headers, timeout=15
        )
        if create_res.status_code == 201:
            return create_res.json()["id"]
        if create_res.status_code == 400:
            term_id = create_res.json().get("data", {}).get("term_id")
            if term_id:
                return term_id
        print(f"⚠️ Category Create Failed ({cat_name}): {create_res.status_code}")
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ Category Processing Fail ({cat_name}): {e}")
    return None


# Clean Value
def _clean(value):
    if isinstance(value, list):
        value = value[0] if value else ""
    return str(value or "").strip().strip(".,;:|\"'")


# Defult Catgories
DEFAULT_GROUPS = [
    (
        ["INTERNATIONAL", "আন্তর্জাতিক", "বিশ্ব"],
        [
            "world",
            "global",
            "foreign",
            "international",
            "diplomacy",
            "war",
            "আন্তর্জাতিক",
            "বিশ্ব",
            "বৈশ্বিক",
            "বিদেশ",
            "কূটনীতি",
            "যুদ্ধ",
        ],
    ),
    (
        ["BUSINES", "অর্থনীতি", "ব্যবসা", "বাণিজ্য"],
        [
            "business",
            "economy",
            "economic",
            "finance",
            "financial",
            "market",
            "stock",
            "trade",
            "banking",
            "অর্থনীতি",
            "অর্থনৈতিক",
            "ব্যবসা",
            "বাণিজ্য",
            "বাজার",
            "শেয়ারবাজার",
            "ব্যাংক",
        ],
    ),
    (
        ["HEALTH", "স্বাস্থ্য"],
        [
            "health",
            "medical",
            "medicine",
            "wellness",
            "disease",
            "hospital",
            "fitness",
            "স্বাস্থ্য",
            "চিকিৎসা",
            "হাসপাতাল",
            "রোগ",
            "ওষুধ",
        ],
    ),
    (
        ["POLITIC", "রাজনীতি"],
        [
            "politics",
            "political",
            "government",
            "election",
            "parliament",
            "policy",
            "রাজনীতি",
            "রাজনৈতিক",
            "সরকার",
            "নির্বাচন",
            "সংসদ",
        ],
    ),
    (
        ["TECHNOLOGY", "প্রযুক্তি"],
        [
            "tech",
            "technology",
            "science",
            "gadget",
            "gadgets",
            "ai",
            "software",
            "internet",
            "প্রযুক্তি",
            "বিজ্ঞান",
            "ইন্টারনেট",
            "সফটওয়্যার",
        ],
    ),
    (
        ["SPORTS", "খেলা", "ক্রীড়া"],
        [
            "sports",
            "sport",
            "cricket",
            "football",
            "soccer",
            "tennis",
            "olympics",
            "game",
            "খেলা",
            "খেলাধুলা",
            "ক্রীড়া",
            "ক্রিকেট",
            "ফুটবল",
            "টেনিস",
            "অলিম্পিক",
        ],
    ),
    (
        ["RELIGION", "ধর্ম"],
        [
            "religion",
            "religious",
            "islam",
            "islamic",
            "imam",
            "mosque",
            "hajj",
            "waqf",
            "ধর্ম",
            "ধর্মীয়",
            "ইসলাম",
            "ইসলামিক",
            "ইমাম",
            "মসজিদ",
            "হজ",
            "ওয়াকফ",
        ],
    ),
    (
        ["ENTERTAINMENT", "বিনোদন"],
        [
            "entertainment",
            "movie",
            "film",
            "cinema",
            "music",
            "drama",
            "celebrity",
            "বিনোদন",
            "সিনেমা",
            "চলচ্চিত্র",
            "গান",
            "নাটক",
        ],
    ),
    (
        ["EDUCATION", "শিক্ষা"],
        [
            "education",
            "school",
            "university",
            "exam",
            "student",
            "শিক্ষা",
            "স্কুল",
            "বিশ্ববিদ্যালয়",
            "পরীক্ষা",
            "শিক্ষার্থী",
        ],
    ),
    (
        ["CRIME", "অপরাধ"],
        [
            "crime",
            "police",
            "murder",
            "arrest",
            "court",
            "অপরাধ",
            "পুলিশ",
            "হত্যা",
            "গ্রেপ্তার",
            "আদালত",
        ],
    ),
    (
        ["LIFESTYLE", "জীবনযাপন"],
        ["lifestyle", "food", "travel", "fashion", "জীবনযাপন", "খাবার", "ভ্রমণ", "ফ্যাশন"],
    ),
]


# Match Filter Categories
def _keywords(entry, include_defaults=True):
    raw = entry.get("Filter", entry.get("Keywords", []))
    if isinstance(raw, str):
        raw = [raw]
    out = []
    for item in raw:
        if isinstance(item, str) and "," in item:
            out += [k.strip().casefold() for k in item.split(",") if k.strip()]
        else:
            out += [str(item).strip().casefold()]
    if include_defaults:
        name = str(entry.get("Category Name", "")).casefold()
        for stems, aliases in DEFAULT_GROUPS:
            if any(stem in name for stem in stems):
                out += [a.casefold() for a in aliases]
    return out


# Match Categories
def _loose_match(a, b):
    a = str(a or "").strip().casefold()
    b = str(b or "").strip().casefold()
    if not a or not b:
        return False
    if a == b:
        return True
    shorter, longer = sorted((a, b), key=len)
    return len(shorter) >= 3 and shorter in longer


# Finding Main Categories
def find_main_entry(config, *texts):
    for text in texts:
        t = str(text or "").strip()
        if not t:
            continue
        for entry in config:
            if _same(entry.get("Category Name"), t) or any(
                _same(k, t) for k in _keywords(entry)
            ):
                return entry
        for entry in config:
            if _loose_match(entry.get("Category Name"), t) or any(
                _loose_match(k, t) for k in _keywords(entry)
            ):
                return entry
        for word in t.split():
            if len(word) < 3:
                continue
            for entry in config:
                if _loose_match(entry.get("Category Name"), word) or any(
                    _loose_match(k, word) for k in _keywords(entry)
                ):
                    return entry
    return None


# Filter & Save "Filter"
def _is_main_itself(entry, sub_name):
    name = str(entry.get("Category Name", "")).strip().casefold()
    sub = sub_name.strip().casefold()
    if _same(name, sub):
        return True
    return _loose_match(name, sub) and len(sub) <= len(name)


# Create Filter
def add_to_filter(main_entry, items_to_add):
    if not items_to_add:
        return

    filter_key = (
        "Filter"
        if "Filter" in main_entry
        else ("Keywords" if "Keywords" in main_entry else "Filter")
    )

    current_filter = main_entry.get(filter_key, [])
    filter_list = []

    if isinstance(current_filter, str):
        filter_list = [
            x.strip().upper() for x in current_filter.split(",") if x.strip()
        ]
    elif isinstance(current_filter, list):
        for item in current_filter:
            if isinstance(item, str) and "," in item:
                filter_list.extend(
                    [x.strip().upper() for x in item.split(",") if x.strip()]
                )
            elif str(item).strip():
                filter_list.append(str(item).strip().upper())

    for new_item in items_to_add:
        if not new_item:
            continue
        item_upper = str(new_item).strip().upper()
        if item_upper and item_upper not in filter_list:
            filter_list.append(item_upper)

    main_entry[filter_key] = filter_list


# Final Tags Return
def get_final_category_ids(
    wp_site_url, auth, headers, ai_category, sub_category=None, tag_names=None
):
    config, site_file = load_site_categories(wp_site_url)

    cat_text = _clean(ai_category)
    sub_name = _clean(sub_category)
    tag_texts = [str(t).strip() for t in (tag_names or []) if t and str(t).strip()]

    main_entry = find_main_entry(config, cat_text, sub_name, *tag_texts)

    if main_entry is None:
        new_name = cat_text or sub_name or DEFAULT_CATEGORY
        new_id = get_or_create_wp_category(
            wp_site_url, auth, headers, new_name, parent_id=0
        )
        if not new_id:
            return []
        main_entry = {"Category Name": new_name.upper(), "ID": new_id, "Filter": []}
        config.append(main_entry)

    if "Category Name" in main_entry:
        main_entry["Category Name"] = str(main_entry["Category Name"]).strip().upper()

    main_id = main_entry.get("ID")
    if not _valid_id(main_id):
        main_id = get_or_create_wp_category(
            wp_site_url, auth, headers, main_entry["Category Name"], parent_id=0
        )
        if not main_id:
            return []
        main_entry["ID"] = main_id
    main_id = _to_int(main_id)

    category_ids = [main_id]
    items_for_filter = []

    if sub_name and not _is_main_itself(main_entry, sub_name):
        sub_name_upper = sub_name.upper()
        items_for_filter.append(sub_name_upper)

        subs = main_entry.setdefault("Sub Categories", [])
        sub_entry = next(
            (s for s in subs if _same(s.get("Name"), sub_name_upper)), None
        )

        sub_id = sub_entry.get("ID") if sub_entry else None
        if not _valid_id(sub_id):
            sub_id = get_or_create_wp_category(
                wp_site_url, auth, headers, sub_name_upper, parent_id=main_id
            )
            if sub_id:
                if sub_entry:
                    sub_entry["ID"] = sub_id
                    sub_entry["Name"] = sub_name_upper
                else:
                    subs.append({"Name": sub_name_upper, "ID": sub_id})
        if sub_id:
            category_ids.append(_to_int(sub_id))

    if tag_texts:
        items_for_filter.extend(tag_texts)

    add_to_filter(main_entry, items_for_filter)

    save_json_file(site_file, config)
    return list(dict.fromkeys(category_ids))


# ---------------- Tags ----------------


def _site_key(wp_site_url):
    return urlparse(wp_site_url).netloc.replace(":", "_") or "site"


# Save Tags In Site Loup json
def load_tags_config(wp_site_url):
    site_file = f"tags_map_{_site_key(wp_site_url)}.json"
    return load_json_file(site_file), site_file


# Create Tags In Json
def get_or_create_wp_tag(wp_site_url, auth, headers, tag_name):
    try:
        tag_name = str(tag_name).strip().upper()
        slug = slugify(tag_name) or None
        base = f"{_api(wp_site_url)}/tags"

        if slug:
            res = requests.get(
                base, params={"slug": slug}, auth=auth, headers=headers, timeout=15
            )
            if res.status_code == 200 and res.json():
                return res.json()[0]["id"]

        payload = {"name": tag_name}
        if slug:
            payload["slug"] = slug
        create_res = requests.post(
            base, json=payload, auth=auth, headers=headers, timeout=15
        )
        if create_res.status_code == 201:
            return create_res.json()["id"]
        if create_res.status_code == 400:
            term_id = create_res.json().get("data", {}).get("term_id")
            if term_id:
                return term_id
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ Tag Processing Fail ({tag_name}): {e}")
    return None


# Final Tags Return With ID
def get_final_tag_ids(wp_site_url, auth, headers, tag_names):
    tag_ids = []
    if not tag_names:
        return tag_ids

    config, site_file = load_tags_config(wp_site_url)

    for tag_name in tag_names:
        if not tag_name or not str(tag_name).strip():
            continue
        tag_name_str = str(tag_name).strip()

        tag_entry = next((i for i in config if i.get("Tag Name") == tag_name_str), None)

        if tag_entry and _valid_id(tag_entry.get("ID")):
            tag_id = tag_entry["ID"]
        else:
            tag_id = get_or_create_wp_tag(wp_site_url, auth, headers, tag_name_str)
            if tag_id:
                if tag_entry:
                    tag_entry["ID"] = tag_id
                    tag_entry["Tag Name"] = tag_name_str
                else:
                    config.append({"Tag Name": tag_name_str, "ID": tag_id})

        if tag_id and tag_id not in tag_ids:
            tag_ids.append(tag_id)

    save_json_file(site_file, config)
    return tag_ids
