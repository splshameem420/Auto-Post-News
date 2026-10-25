import json
import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from Platform.blogger_publisher import publish_post
from Platform.wordpress_publisher import publish_wp_post

SCOPES = ["https://www.googleapis.com/auth/blogger"]
TARGETS_FILE = "Site.json"
STATE_FILE = "rotation_state.json"

def load_targets():
    if os.path.exists(TARGETS_FILE):
        try:
            with open(TARGETS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:  # noqa: BLE001
            print(f"❌ Site.json Red Problem: {e}")
            return []
    else:
        print(f"⚠️ Site.json Missing : {TARGETS_FILE}")
    return []

def load_index():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("next_index", 0)
        except Exception:  # noqa: BLE001
            return 0
    return 0

def save_index(i):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"next_index": i}, f)

def resolve_value(key_or_list):
    """Environment variable ba direct list/string theke value resolve korar helper function"""
    if isinstance(key_or_list, list):
        for item in key_or_list:
            env_val = os.environ.get(item)
            if env_val:
                return env_val
        if len(key_or_list) > 1:
            return key_or_list[-1]
        return None
    elif isinstance(key_or_list, str):
        return os.environ.get(key_or_list) or key_or_list
    return None

def get_blogger_service(target):
    creds = None
    env_config = target.get("environment", {})
    token_input = env_config.get("token_env")
    
    token_str = resolve_value(token_input)
    if token_str:
        try:
            token_data = json.loads(token_str)
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        except Exception as e:  # noqa: BLE001
            print(f"⚠️ Blogger Token Error {target.get('Name')}: {e}")
            
    if not creds and os.path.exists("token.json"):
        try:
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        except Exception:  # noqa: BLE001, S110
            pass

    return build("blogger", "v3", credentials=creds)

def post_blogger(target, ai_data, image):
    service = get_blogger_service(target)
    env_config = target.get("environment", {})
    blog_id_input = env_config.get("blog_id_env")
    
    blog_id = resolve_value(blog_id_input)
    
    if not blog_id:
        raise Exception(f"Blog ID not found for {target.get('Name')}")  # noqa: TRY002

    # Blogger-এ ক্যাটাগরি = লেবেল, তাই ক্যাটাগরি + ট্যাগ একসাথে লেবেল হিসেবে যাবে
    labels = [ai_data.get("category"), ai_data.get("sub_category")] + ai_data.get("tags", [])
    labels = list(dict.fromkeys(l for l in labels if l))

    resp = publish_post(
        service,
        blog_id,
        ai_data["title"],
        ai_data["content"],
        image,
        labels,
    )
    if resp and "url" in resp:
        return resp.get("url")
    raise Exception("Blogger publishing failed to return URL.")  # noqa: TRY002

def post_wordpress(target, ai_data, image):
    env_config = target.get("environment", {})
    user_input = env_config.get("user_env")
    pass_input = env_config.get("pass_env")
    
    username = resolve_value(user_input)
    app_password = resolve_value(pass_input)
    wp_site_url = target.get("Site_Url") or target.get("Url")

    if not username or not app_password or not wp_site_url:
        raise Exception(f"WordPress credentials or URL missing for {target.get('Name')}")  # noqa: TRY002

    resp = publish_wp_post(
        wp_site_url=wp_site_url,
        username=username,
        app_password=app_password,
        title=ai_data['title'], 
        content=ai_data['content'], 
        image_url=image, 
        scraped_category=ai_data.get('category', None),
        sub_category=ai_data.get('sub_category', None),
        tags=ai_data.get('tags', [])
    )
    
    if resp and "link" in resp:
        return resp.get("link")
    raise Exception("WordPress publishing failed to return post link.")  # noqa: TRY002

def publish_final_post(ai_data, image):
    targets = load_targets()
    if not targets:
        print("⚠️ No targets found in Site.json!")
        return False, None, None

    n = len(targets)
    start = load_index() % n

    for step in range(n):
        idx = (start + step) % n
        t = targets[idx]
        site_name = t.get("Name", "Unknown Site")
        platform = t.get("Platform", "")
        
        try:
            print(f"🔄 Trying to post on [{site_name}] ({platform})...")
            if platform.lower() == "blogger":
                url = post_blogger(t, ai_data, image)
            elif platform.lower() == "wordpress":
                url = post_wordpress(t, ai_data, image)
            else:
                print(f"⚠️ Unknown platform: {platform}")
                continue
            
            save_index((idx + 1) % n)  
            return True, site_name, url
            
        except Exception as e:  # noqa: BLE001
            print(f"⚠️ [{site_name}] Post failed: {e}")
            continue

    return False, None, None