import time
from database.sqlite_db import NewsDatabase
from crawler.naver import NaverNewsCrawler
from summarizer.engine import Summarizer
from processor.clusterer import IssueClusterer
from processor.scorer import IssueScorer
from processor.generator import ContentGenerator
from processor.image_gen import ImageGenerator
from notification.telegram import TelegramNotifier

def main():
    print("Initializing News Factory System (Full Pipeline)...")
    db = NewsDatabase()
    crawler = NaverNewsCrawler()
    summarizer = Summarizer()
    clusterer = IssueClusterer(threshold=0.7)
    scorer = IssueScorer()
    generator = ContentGenerator()
    image_gen = ImageGenerator()
    notifier = TelegramNotifier()
    
    MAX_PAGES = 1
    TARGET_COUNT = 20
    new_count = 0
    total_fetched = 0
    
    print(f"Starting pipeline at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    active_issues = db.get_active_issues(hours=24)
    
    for page in range(1, MAX_PAGES + 1):
        print(f"\n>>> Crawling Page {page}...")
        news_list, should_stop = crawler.fetch_news(page=page)
        
        if not news_list: break
            
        for news in news_list:
            total_fetched += 1
            if news.full_content:
                news.snippet = summarizer.summarize(news.full_content)
            
            issue_id = clusterer.find_best_matching_issue(news, active_issues)
            if issue_id:
                news.issue_id = issue_id
            else:
                issue_id = db.create_issue(news.title)
                news.issue_id = issue_id
                active_issues.append({"id": issue_id, "representative_title": news.title})
            
            if db.insert_news(news):
                new_count += 1
        
        if should_stop: break
        time.sleep(1)
    
    print("-" * 30)
    print(f"Fetch completed. Unique new items: {new_count}")
    
    # 4. Scoring & Content Generation
    print("\n[🥇 Trending Issues & IG Content]")
    top_issues = scorer.select_top_issues(db, threshold=1.0)
    
    for i, issue in enumerate(top_issues[:3]):
        # Generate IG candidates
        content = generator.generate_instagram_content(issue['representative_title'], issue['representative_title'])
        images = [] # 이미지는 발행 시 실시간 생성합니다.
        
        # Save to DB
        db.update_issue_candidates(issue['id'], content['summary'], content['titles'], images)
        
        print(f"{i+1}. {issue['representative_title']}")
        print(f"   Score: {issue['score']} | Content Generated ✅")
        
        # 5. Telegram Notification (Optional: for the top issue only)
        if i == 0 and issue['score'] >= 1.2: # Threshold for alert
            if notifier.send_issue_alert(issue['representative_title'], issue['score'], issue['stats']['article_count']):
                print("   Telegram Alert Sent! 📨")
    
    print("-" * 30)
    print(f"Process completed successfully.")
    
    # Print some stats from DB
    all_news = db.get_all_news()
    print(f"Total entries in database: {len(all_news)}")

if __name__ == "__main__":
    main()
