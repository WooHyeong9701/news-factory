from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from database.sqlite_db import NewsDatabase
from social.instagram import InstagramPublisher
from notification.telegram import TelegramNotifier
from processor.fact_checker import FactChecker
from processor.generator import ContentGenerator
from processor.image_gen import ImageGenerator
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
app.mount("/static", StaticFiles(directory="web/static"), name="static")
db = NewsDatabase()
publisher = InstagramPublisher()
notifier = TelegramNotifier()
fact_checker = FactChecker()
generator = ContentGenerator()
image_gen = ImageGenerator()
templates = Jinja2Templates(directory="web/templates")

@app.get("/regenerate_title")
async def regenerate_title(issue_id: int):
    """제목이 마음에 들지 않을 때 AI에게 다시 생성을 요청합니다."""
    issue = db.get_issue_by_id(issue_id)
    if not issue:
        return {"status": "error", "message": "Issue not found"}
    
    # AI를 통해 새로운 제목 생성
    result = generator.generate_instagram_content(issue['representative_title'], issue['summary_candidate'])
    new_title = result.get("titles", [issue['representative_title']])[0]
    
    return {"status": "success", "title": new_title}

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
scheduler.add_job(crawl_job, 'interval', minutes=30)
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

@app.post("/review_images", response_class=HTMLResponse)
async def review_images(request: Request, issue_id: int = Form(...), final_title: str = Form(...)):
    """게시 전 이미지를 생성하고 사용자가 선택할 수 있게 합니다."""
    print(f"🎨 리뷰용 이미지 생성 시작: {final_title}")
    # 요청하신 대로 3장의 후보를 생성합니다.
    images = image_gen.generate_news_images(final_title, count=3)
    
    return templates.TemplateResponse("review.html", {
        "request": request,
        "issue_id": issue_id,
        "title": final_title,
        "images": images
    })

@app.post("/select", response_class=HTMLResponse)
async def select_issue(request: Request, issue_id: int = Form(...), selected_title: str = Form(...), selected_image: str = Form(...)):
    """리뷰 페이지에서 선택한 최종 이미지와 제목으로 업로드를 완료합니다."""
    issue = db.get_issue_by_id(issue_id)
    caption = f"{selected_title}\n\n{issue['summary_candidate']}"
    
    # [변경] 이미지는 이전 단계에서 생성되었으므로, 선택된 것을 그대로 사용합니다.
    success = publisher.publish_post(selected_image, caption)
    
    if success:
        db.mark_issue_published(issue_id, selected_title, selected_image)
        msg = f"🚀 '{selected_title}' 게시물이 인스타그램에 성공적으로 공유되었습니다!"
    else:
        msg = f"❌ 인스타그램 업로드 중 오류가 발생했습니다."

    return await read_index(request, msg=msg)

@app.post("/delete")
async def delete_issue_route(issue_id: int = Form(...)):
    db.delete_issue(issue_id)
    return {"status": "success", "message": f"Issue {issue_id} deleted"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
