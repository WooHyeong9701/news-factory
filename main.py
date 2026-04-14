import time
from database.sqlite_db import NewsDatabase
from crawler.naver import NaverNewsCrawler
from summarizer.engine import Summarizer

def main():
    print("Initializing News Factory System...")
    db = NewsDatabase()
    crawler = NaverNewsCrawler()
    summarizer = Summarizer()
    
    print(f"Starting deep crawl and summarization at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    news_list = crawler.fetch_news()
    
    new_count = 0
    for news in news_list:
        # Generate high-quality summary from full content
        if news.full_content:
            news.snippet = summarizer.summarize(news.full_content)
        
        if db.insert_news(news):
            new_count += 1
            print(f"[New] {news.publisher}: {news.title}")
            print(f"      Summary: {news.snippet[:100]}...")
    
    print("-" * 30)
    print(f"Process completed. {new_count} new items summarized and saved.")
    
    # Print some stats from DB
    all_news = db.get_all_news()
    print(f"Total entries in database: {len(all_news)}")

if __name__ == "__main__":
    main()
