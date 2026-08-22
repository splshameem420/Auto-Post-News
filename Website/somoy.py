import feedparser
import newspaper
import requests


def get_real_url(google_url):
    try:
        response = requests.get(google_url, timeout=5, allow_redirects=True)
        return response.url
    except Exception:  # noqa: BLE001
        return google_url

def scrape_somoy(visited_urls, config):
    feed_url = 'https://news.google.com/rss/search?q=site:somoynews.tv&hl=bn&gl=BD&ceid=BD:bn'
    feed = feedparser.parse(feed_url)
    news_items = []

    for entry in feed.entries[:5]:
        real_url = get_real_url(entry.link)
        if real_url in visited_urls or entry.link in visited_urls:
            continue

        try:
            article = newspaper.Article(real_url, config=config)
            article.download()
            article.parse()

            text = article.text.strip()
            if len(text) > 100:
                news_items.append({
                    'title': entry.title.replace(' - সময় নিউজ', '').strip(),
                    'text': text,
                    'url': real_url,
                    'image': article.top_image if article.top_image else None
                })
        except Exception as e:  # noqa: BLE001
            print(f"Error scraping Somoy TV ({real_url}): {e}")

    return news_items