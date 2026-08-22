import feedparser
import newspaper


def scrape_bbc(visited_urls, config):
    feed_url = 'https://feeds.bbci.co.uk/bengali/rss.xml'
    feed = feedparser.parse(feed_url)
    news_items = []

    for entry in feed.entries[:5]:
        if entry.link in visited_urls:
            continue

        try:
            article = newspaper.Article(entry.link, config=config)
            article.download()
            article.parse()

            text = article.text.strip()
            if len(text) > 100:
                news_items.append({
                    'title': entry.title,
                    'text': text,
                    'url': entry.link,
                    'image': article.top_image if article.top_image else None
                })
        except Exception as e:  # noqa: BLE001
            print(f"Error scraping BBC Bangla ({entry.link}): {e}")

    return news_items