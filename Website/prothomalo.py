import feedparser
import newspaper


def scrape_prothomalo(visited_urls, config):
    """
    প্রথম আলো (Prothom Alo) এর RSS Feed থেকে নতুন খবর সংগ্রহের ফাংশন।
    """
    feed_url = 'https://www.prothomalo.com/feed'
    feed = feedparser.parse(feed_url)
    news_items = []

    for entry in feed.entries[:3]:
        if entry.link in visited_urls or entry.link.endswith('.pdf'):
            continue

        try:
            article = newspaper.Article(entry.link, config=config)
            article.download()
            article.parse()

            if len(article.text) > 150:
                news_items.append({
                    'title': entry.title,
                    'text': article.text,
                    'url': entry.link,
                    'image': article.top_image if article.top_image else None
                })
        except Exception as e:  # noqa: BLE001
            print(f"Error scraping Prothom Alo ({entry.link}): {e}")

    return news_items