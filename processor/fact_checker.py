import requests
from bs4 import BeautifulSoup
import urllib.parse

class FactChecker:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def check_for_fake_news_reports(self, issue_title: str) -> dict:
        """
        Searches Naver News for 'fake news', 'erroneous report' keywords along with the issue title.
        Returns a dict with positive status and found links.
        """
        keywords = ["가짜뉴스", "오보", "정정보고", "사실무근"]
        search_query = f'"{issue_title}" ' + " OR ".join(keywords)
        encoded_query = urllib.parse.quote(search_query)
        url = f"https://search.naver.com/search.naver?where=news&query={encoded_query}"

        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "lxml")
            
            # Simple heuristic: If search results exist, it might be a problem
            news_items = soup.select("ul.list_news li.bx")
            if len(news_items) > 0:
                return {
                    "is_suspicious": True,
                    "count": len(news_items),
                    "evidence_link": url,
                    "top_news": news_items[0].select_one("a.news_tit").text if news_items[0].select_one("a.news_tit") else ""
                }
        except Exception as e:
            print(f"Fact Check Error for {issue_title}: {e}")
            
        return {"is_suspicious": False}
