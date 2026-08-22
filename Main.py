import json
import os
import time

import newspaper
from google import genai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from Publisher.blogger_publisher import publish_post
from Rewrite.ai_rewriter import rewrite_article

# আপনার প্রজেক্ট স্ট্রাকচার অনুযায়ী মডিউল ইম্পোর্ট
from Website.aljazeera import scrape_aljazeera
from Website.bbc import scrape_bbc
from Website.bd_pratidin import scrape_bd_pratidin
from Website.jagonews import scrape_jagonews
from Website.jamuna import scrape_jamuna
from Website.prothomalo import scrape_prothomalo
from Website.somoy import scrape_somoy
from Website.tsports import scrape_tsports

# ==================== ১. কনফিগারেশন ====================
# লোকাল টেস্টের জন্য কোটেশনের ভেতরে আপনার Key ও Blog ID সরাসরি বসান
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
BLOG_ID = os.environ.get("BLOG_ID")

VISITED_LOG = 'visited_urls.json'
SCOPES = ['https://www.googleapis.com/auth/blogger']

# Gemini Client ইনিশিয়ালাইজেশন
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# Newspaper ব্রাউজার কনফিগারেশন (403 Error এড়ানোর জন্য)
config = newspaper.Config()
config.browser_user_agent = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/120.0.0.0 Safari/537.36'
)
config.request_timeout = 15

# ==================== ২. হেলপার ফাংশন ====================
def get_visited_urls():
    """পূর্বে ভিজিট করা খবরগুলোর URL তালিকা রিড করার ফাংশন"""
    if os.path.exists(VISITED_LOG):
        try:
            with open(VISITED_LOG, 'r') as f:
                return json.load(f)
        except Exception:  # noqa: BLE001
            return []
    return []

def save_visited_url(url):
    urls = get_visited_urls()
    urls.append(url)
    with open(VISITED_LOG, 'w') as f:
        json.dump(urls, f)

def get_blogger_service():
    """
    Blogger API সার্ভিস কানেক্ট করার ফাংশন।
    - GitHub Actions environment থাকলে BLOGGER_TOKEN ব্যবহার করবে।
    - লোকাল এনভায়রনমেন্টে token.json ব্যবহার করবে।
    """
    creds = None
    if os.environ.get('BLOGGER_TOKEN'):
        token_data = json.loads(os.environ.get('BLOGGER_TOKEN'))
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
    elif os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    return build('blogger', 'v3', credentials=creds)

# ==================== ৩. মূল এক্সিকিউশন ====================
if __name__ == '__main__':
    print("🚀 [Auto News Poster] রান হচ্ছে...")
    service = get_blogger_service()
    visited = get_visited_urls()

    scrapers = [
        ("BD Pratidin", scrape_bd_pratidin),
        ("Prothom Alo", scrape_prothomalo),
        ("Aljazeera", scrape_aljazeera),
        ("Somoy", scrape_somoy),
        ("Tsports", scrape_tsports),
        ("Jagonews", scrape_jagonews),
        ("Jamuna", scrape_jamuna),
        ("BBC Bangla", scrape_bbc)
    ]

    for site_name, scrape_func in scrapers:
        print(f"\n🔍 [{site_name}] RSS ফিড থেকে খবর স্ক্র্যাপ করা হচ্ছে...")
        news_list = scrape_func(visited, config)

        if not news_list:
            print(f"⚠️ [{site_name}] কোনো নতুন খবর পাওয়া যায়নি।")
            continue

        for news in news_list:
            print(f"\n📰 New Post Found {news['title']}")
            print("🤖 Gemini AI Will Rewriting...")
            
            ai_data = rewrite_article(ai_client, news['title'], news['text'])

            print("📤 Posting On Blogger...")
            response = publish_post(
                service, 
                BLOG_ID, 
                ai_data['title'], 
                ai_data['content'], 
                news['image'], 
                ai_data.get('tags', [])
            )
            
            post_url = response.get('url', 'N/A')
            print(f"✅ Sucsess To Post On Blogger {post_url}")
            
            save_visited_url(news['url'])
            time.sleep(10)
