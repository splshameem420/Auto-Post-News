import cloudscraper
import feedparser
import newspaper


def scrape_jagonews(visited_urls, config):
    feed_url = 'https://www.jagonews24.com/rss/rss.xml'
    feed = feedparser.parse(feed_url)
    news_items = []
    
    # ক্লাউডফ্লায়ার বাইপাস করার জন্য স্ক্র্যাপার তৈরি করা হলো
    scraper = cloudscraper.create_scraper()

    for entry in feed.entries[:5]:
        if entry.link in visited_urls:
            continue

        try:
            # সরাসরি article.download() না করে cloudscraper দিয়ে HTML ফেচ করা হচ্ছে
            response = scraper.get(entry.link, headers=config.browser_user_agent, timeout=15)
            
            if response.status_code == 200:
                article = newspaper.Article(entry.link, config=config)
                # ফেচ করা HTML সরাসরি newspaper-এ ইনপুট দেওয়া হচ্ছে
                article.download(input_html=response.text)
                article.parse()

                text = article.text.strip()
                if len(text) > 100:
                    news_items.append({
                        'title': entry.title,
                        'text': text,
                        'url': entry.link,
                        'image': article.top_image if article.top_image else None
                    })
            else:
                print(f"Error scraping Jago News ({entry.link}): HTTP Status {response.status_code}")
                
        except Exception as e:  # noqa: BLE001
            print(f"Error scraping Jago News ({entry.link}): {e}")

    return news_items