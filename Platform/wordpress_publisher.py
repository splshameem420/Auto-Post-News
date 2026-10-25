import requests
from requests.auth import HTTPBasicAuth

from Categories.Categories2 import get_final_category_ids, get_final_tag_ids


def upload_image_to_wp(wp_site_url, auth, headers, image_url):
    try:
        img_res = requests.get(image_url, timeout=15)
        if img_res.status_code == 200:
            file_name = image_url.split("/")[-1].split("?")[0]
            if not file_name or "." not in file_name:
                file_name = "featured_image.jpg"
            
            media_headers = headers.copy()
            if 'Content-Type' in media_headers:
                del media_headers['Content-Type']
            
            files = {'file': (file_name, img_res.content)}
            media_res = requests.post(f"{wp_site_url}/wp-json/wp/v2/media", files=files, auth=auth, headers=media_headers, timeout=30)
            
            if media_res.status_code == 201:
                return media_res.json()['id']
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ Image Upload Error {e}")
    return None

def publish_wp_post(wp_site_url, username, app_password, title, content, image_url=None, scraped_category=None, tags=None, sub_category=None):
    api_url = f"{wp_site_url.rstrip('/')}/wp-json/wp/v2/posts"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": f"{wp_site_url}/",
        "Content-Type": "application/json"
    }
    auth = HTTPBasicAuth(username, app_password)
    
    featured_media_id = None
    if image_url:
        print("🖼️ Wordpress Image Uploading...")
        featured_media_id = upload_image_to_wp(wp_site_url, auth, headers, image_url)

    category_ids = get_final_category_ids(wp_site_url, auth, headers, scraped_category, sub_category)
    tag_ids = get_final_tag_ids(wp_site_url, auth, headers, tags)

    formatted_content = content.replace("\n", "<br>")
    
    payload = {
        'title': title,
        'content': formatted_content,
        'status': 'publish',
    }
    
    if featured_media_id:
        payload['featured_media'] = featured_media_id
        
    if category_ids:
        payload['categories'] = category_ids

    if tag_ids:
        payload['tags'] = tag_ids

    try:
        response = requests.post(api_url, json=payload, auth=auth, headers=headers, timeout=30)
        
        if response.status_code == 201:
            return response.json()
        else:
            print(f"⚠️ Wordpress Post Error : {response.status_code} - {response.text[:300]}")
            return None
            
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ Connection Error : {e}")
        return None