import time
from database.sqlite_db import NewsDatabase
from crawler.naver import NaverNewsCrawler

def main():
    print("Initializing News Crawler...")
    db = NewsDatabase()
    crawler = NaverNewsCrawler()
    
    print(f"Starting crawl at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # In a real scenario, this could be in a loop or scheduled
    news_list = crawler.fetch_news()
    
    new_count = 0
    for news in news_list:
        if db.insert_news(news):
            new_count += 1
            print(f"[New] {news.publisher}: {news.title}")
    
    print("-" * 30)
    print(f"Fetch completed. Found {len(news_list)} items, {new_count} new items saved.")
    
    # Print some stats from DB
    all_news = db.get_all_news()
    print(f"Total entries in database: {len(all_news)}")

if __name__ == "__main__":
    main()
