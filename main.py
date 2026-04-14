import time
from database.sqlite_db import NewsDatabase
from crawler.naver import NaverNewsCrawler
from summarizer.engine import Summarizer

def main():
    print("Initializing News Factory System...")
    db = NewsDatabase()
    crawler = NaverNewsCrawler()
    summarizer = Summarizer()
    
    MAX_PAGES = 25
    TARGET_COUNT = 500
    new_count = 0
    total_fetched = 0
    
    print(f"Starting expanded crawl at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    for page in range(1, MAX_PAGES + 1):
        print(f"\n>>> Crawling Page {page}...")
        news_list, should_stop = crawler.fetch_news(page=page)
        
        if not news_list:
            print("No more news found on this page.")
            break
            
        for news in news_list:
            total_fetched += 1
            # Generate summary
            if news.full_content:
                news.snippet = summarizer.summarize(news.full_content)
            
            if db.insert_news(news):
                new_count += 1
                if new_count % 10 == 0:
                    print(f"Progress: {new_count} new items saved...")
            
            if new_count >= TARGET_COUNT:
                print(f"Reached target count of {TARGET_COUNT}. Stopping.")
                should_stop = True
                break
        
        if should_stop:
            print("Time limit reached or target met. Stopping crawl.")
            break
            
        # Delay between pages
        time.sleep(1)
    
    print("-" * 30)
    print(f"Process completed.")
    print(f"- Total processed: {total_fetched}")
    print(f"- Unique new items saved: {new_count}")
    
    # Print some stats from DB
    all_news = db.get_all_news()
    print(f"Total entries in database: {len(all_news)}")

if __name__ == "__main__":
    main()
