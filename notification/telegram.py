import requests
import os

class TelegramNotifier:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    def is_enabled(self):
        return bool(self.token and self.chat_id)

    def send_issue_alert(self, issue_title: str, score: float, article_count: int):
        if not self.is_enabled():
            print("\n[!] Telegram Notifier is not configured. Skipping alert.")
            return False

        message = (
            "🔔 **새로운 이슈 분석 완료!**\n\n"
            f"📌 **이슈명**: {issue_title}\n"
            f"📈 **트렌딩 점수**: {score}\n"
            f"📰 **관련 기사수**: {article_count}개\n\n"
            "📱 지금 모바일 웹사이트에서 검토 후 인스타에 업로드하세요!"
        )

        try:
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            response = requests.post(self.api_url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            return False
