import requests
from requests.auth import HTTPBasicAuth


def get_or_create_category(wp_site_url, auth, headers, cat_name):
    """ক্যাটাগরি না থাকলে তৈরি করবে এবং আইডি রিটার্ন করবে"""
    try:
        # ক্যাটাগরি আগে থেকে আছে কি না চেক করা
        res = requests.get(f"{wp_site_url}/wp-json/wp/v2/categories?search={cat_name}", auth=auth, headers=headers, timeout=15)
        if res.status_code == 200:
            cats = res.json()
            for cat in cats:
                if cat['name'].lower() == cat_name.lower():
                    return cat['id']
        
        # না থাকলে নতুন তৈরি করা
        create_res = requests.post(f"{wp_site_url}/wp-json/wp/v2/categories", json={'name': cat_name}, auth=auth, headers=headers, timeout=15)
        if create_res.status_code == 201:
            return create_res.json()['id']
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ ক্যাটাগরি প্রসেসিং ত্রুটি ({cat_name}): {e}")
    return None

def upload_image_to_wp(wp_site_url, auth, headers, image_url):
    """ছবির লিংক থেকে ডাউনলোড করে ওয়ার্ডপ্রেস মিডিয়া লাইব্রেরিতে আপলোড করবে এবং ID রিটার্ন করবে"""
    try:
        img_res = requests.get(image_url, timeout=15)
        if img_res.status_code == 200:
            file_name = image_url.split("/")[-1].split("?")[0]
            if not file_name or "." not in file_name:
                file_name = "featured_image.jpg"
            
            media_headers = headers.copy()
            if 'Content-Type' in media_headers:
                del media_headers['Content-Type'] # Multipart ফর্ম-ডেটার জন্য কনটেন্ট টাইপ রিমুভ করতে হয়
            
            files = {'file': (file_name, img_res.content)}
            media_res = requests.post(f"{wp_site_url}/wp-json/wp/v2/media", files=files, auth=auth, headers=media_headers, timeout=30)
            
            if media_res.status_code == 201:
                return media_res.json()['id']
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ ইমেজ আপলোড এরর: {e}")
    return None

def publish_wp_post(wp_site_url, username, app_password, title, content, image_url=None, categories=None, tags=None):
    """
    WordPress REST API ব্যবহার করে ফিচারড ইমেজ, ক্যাটাগরি এবং ট্যাগসহ পোস্ট পাবলিশ করার ফাংশন।
    """
    api_url = f"{wp_site_url.rstrip('/')}/wp-json/wp/v2/posts"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": f"{wp_site_url}/",
        "Content-Type": "application/json"
    }
    auth = HTTPBasicAuth(username, app_password)
    
    # ১. ফিচারড ইমেজ আপলোড এবং আইডি সংগ্রহ
    featured_media_id = None
    if image_url:
        print("🖼️ ওয়ার্ডপ্রেস মিডিয়া লাইব্রেরিতে ছবি আপলোড করা হচ্ছে...")
        featured_media_id = upload_image_to_wp(wp_site_url, auth, headers, image_url)

    # ২. ক্যাটাগরি প্রসেসিং (নাম থেকে আইডি বের করা)
    category_ids = []
    if categories:
        if isinstance(categories, str):
            categories = [categories]
        for cat_name in categories:
            cat_id = get_or_create_category(wp_site_url, auth, headers, cat_name)
            if cat_id:
                category_ids.append(cat_id)

    # ৩. কন্টেন্ট ফরম্যাটিং
    formatted_content = content.replace("\n", "<br>")
    
    # ওয়ার্ডপ্রেস পোস্ট পেইল্ড
    payload = {
        'title': title,
        'content': formatted_content,
        'status': 'publish',
    }
    
    if featured_media_id:
        payload['featured_media'] = featured_media_id
        
    if category_ids:
        payload['categories'] = category_ids

    try:
        response = requests.post(api_url, json=payload, auth=auth, headers=headers, timeout=30)
        
        if response.status_code == 201:
            return response.json()
        else:
            print(f"⚠️ ওয়ার্ডপ্রেস পোস্ট ত্রুটি: {response.status_code} - {response.text[:300]}")
            return None
            
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ কানেকশন এরর: {e}")
        return None