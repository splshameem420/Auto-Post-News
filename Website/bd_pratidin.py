import feedparser
import newspaper


def scrape_bd_pratidin(visited_urls, config):
    """
    বাংলাদেশ প্রতিদিন (BD Pratidin) এর RSS Feed থেকে নতুন খবর সংগ্রহের ফাংশন।
    """
    feed_url = 'https://www.bd-pratidin.com/rss.xml'
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
            print(f"Error scraping BD Pratidin ({entry.link}): {e}")

    return news_items