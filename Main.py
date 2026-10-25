import io
import json
import os
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import newspaper
from google import genai
from groq import Groq

from Publisher.universal_publisher import publish_final_post
from Rewrite.ai_rewriter_2 import rewrite_article
from Website.aljazeera import scrape_aljazeera
from Website.bbc import scrape_bbc
from Website.bd_pratidin import scrape_bd_pratidin
from Website.jagonews import scrape_jagonews
from Website.jamuna import scrape_jamuna
from Website.prothomalo import scrape_prothomalo
from Website.somoy import scrape_somoy
from Website.tsports import scrape_tsports

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

VISITED_LOG = 'visited_urls.json'

gemini_client = genai.Client(api_key=GEMINI_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)


config = newspaper.Config()
config.browser_user_agent = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/120.0.0.0 Safari/537.36'
)
config.request_timeout = 15


def get_visited_urls():
    """Older Visited Urls Logs"""
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



if __name__ == '__main__':
    print("🚀 [Auto News Poster] Running...")
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
        print(f"\n🔍 [{site_name}] Post Scraping...")
        news_list = scrape_func(visited, config)

        if not news_list:
            print(f"⚠️ [{site_name}] No New Post Found")
            continue

        for news in news_list:
            print(f"\n📰 New Post Found {news['title']}")
            print("🤖 AI Will Rewriting...")
            
            ai_data = rewrite_article(gemini_client, groq_client, news['title'], news['text'])
            
            if ai_data.get('failed'):
                print("⚠️ Ai Rewrite Failed Skipping Post")
                time.sleep(10)
                continue
            
            print("📤 Posting On...")
            
            ok, target_name, post_url = publish_final_post(ai_data, news['image'])
            
            if not ok:
                print("All Post Fail Skip")
                continue
            
            print(f"✅ Success To Post {post_url}")
            
            save_visited_url(news['url'])
            time.sleep(10)
