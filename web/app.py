from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from database.sqlite_db import NewsDatabase
from social.instagram import InstagramPublisher
from notification.telegram import TelegramNotifier
from processor.fact_checker import FactChecker
from apscheduler.schedulers.background import BackgroundScheduler
from main import main as crawl_job
import json
import uvicorn
import os
import requests
from dotenv import load_dotenv

# 로컬 .env 파일의 환경변수를 불러옵니다.
load_dotenv()

app = FastAPI()
db = NewsDatabase()
publisher = InstagramPublisher()
notifier = TelegramNotifier()
fact_checker = FactChecker()
templates = Jinja2Templates(directory="web/templates")

def monitor_published_issues():
    """Scheduled task to check for fake news reports on published issues."""
    print("🔍 Running Fact-Check Monitor...")
    all_issues = db.get_issues_with_candidates()
    # Check issues published
    published = [i for i in all_issues if i['is_published']]
    
    for issue in published:
        result = fact_checker.check_for_fake_news_reports(issue['representative_title'])
        if result.get("is_suspicious"):
            msg = (
                f"🚨 **가짜뉴스/오보 의심 알림** 🚨\n\n"
                f"📌 **대상**: {issue['selected_title']}\n"
                f"🔎 **발견된 정황**: {result['top_news']}\n"
                f"🔗 [증거 확인]({result['evidence_link']})\n\n"
                "⚠️ 지금 즉시 웹 어드민에서 게시글을 검토하고 삭제하세요!"
            )
            # Direct telegram call for emergency
            token = os.getenv("TELEGRAM_BOT_TOKEN")
            chat_id = os.getenv("TELEGRAM_CHAT_ID")
            if token and chat_id:
                requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                             json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})

# Initialize and start scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(crawl_job, 'interval', hours=1)
scheduler.add_job(monitor_published_issues, 'interval', hours=2)

@app.on_event("startup")
def startup_event():
    print("🚀 Web Server and Scheduler Started!")
    scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request, msg: str = None):
    all_issues = db.get_issues_with_candidates()
    review_issues = [i for i in all_issues if not i['is_published']]
    published_issues = [i for i in all_issues if i['is_published']]
    
    for issue in review_issues:
        if issue['title_candidates']:
            issue['titles'] = json.loads(issue['title_candidates'])
        if issue['image_paths']:
            issue['images'] = json.loads(issue['image_paths'])
            
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "issues": review_issues, 
        "published": published_issues,
        "msg": msg
    })

@app.post("/select", response_class=HTMLResponse)
async def select_issue(request: Request, issue_id: int = Form(...), selected_title: str = Form(...), selected_image: str = Form(...)):
    issue = db.get_issue_by_id(issue_id)
    caption = f"{selected_title}\n\n{issue['summary_candidate']}"
    success = publisher.publish_post(selected_image, caption)
    
    if success:
        db.mark_issue_published(issue_id, selected_title, selected_image)
        msg = f"🚀 이슈 #{issue_id}가 인스타그램에 업로드되었습니다!"
    else:
        msg = f"❌ 인스타그램 업로드 중 오류가 발생했습니다."

    return await read_index(request, msg=msg)

@app.post("/delete", response_class=HTMLResponse)
async def delete_issue_route(request: Request, issue_id: int = Form(...)):
    db.delete_issue(issue_id)
    return await read_index(request, msg=f"🗑️ 광속 삭제! 이슈 #{issue_id}와 모든 기록이 제거되었습니다.")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
