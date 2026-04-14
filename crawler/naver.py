import requests
from bs4 import BeautifulSoup
from typing import List, Tuple
from models.news import NewsItem
from crawler.base import BaseCrawler

import re

import json

from datetime import datetime, timedelta
import time

class NaverNewsCrawler(BaseCrawler):
    def __init__(self):
        self.base_url = "https://news.naver.com/main/list.naver?mode=LSD&mid=sec&sid1=001"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    @property
    def source_name(self) -> str:
        return "Naver"

    def fetch_news(self, page: int = 1) -> Tuple[List[NewsItem], bool]:
        """
        Fetch news for a specific page.
        Returns (list of items, should_stop_pagination)
        """
        news_items = []
        should_stop = False
        url = f"{self.base_url}&page={page}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "lxml")
            list_containers = soup.select("ul.type06_headline li") + soup.select("ul.type06 li")

            if not list_containers:
                return [], True
                
            for item in list_containers:
                try:
                    dt_tags = item.find_all("dt")
                    title_tag = dt_tags[-1].find("a")
                    title = title_tag.text.strip()
                    url = title_tag["href"]
                    
                    snippet_tag = item.find("span", class_="lede")
                    original_snippet = snippet_tag.text.strip() if snippet_tag else ""
                    
                    publisher_tag = item.find("span", class_="writing")
                    publisher = publisher_tag.text.strip() if publisher_tag else "Unknown"
                    
                    date_tag = item.find("span", class_="date")
                    date_str = date_tag.text.strip() if date_tag else ""
                    
                    # Check if news is within 1 hour
                    if not self._is_within_one_hour(date_str):
                        should_stop = True
                        break # Stop parsing this page
                    
                    # Deep Crawling
                    full_content = self._fetch_full_content(url)
                    cleaned_content = self._clean_text(full_content)
                    
                    # Metadata Collection
                    meta = self._fetch_metadata(url)
                    
                    news_items.append(NewsItem(
                        title=title,
                        snippet=original_snippet,
                        publisher=publisher,
                        published_at=date_str,
                        url=url,
                        full_content=cleaned_content,
                        comment_count=meta.get("comment_count", 0),
                        reaction_count=meta.get("reaction_count", 0),
                        reaction_detail=json.dumps(meta.get("reaction_detail", {}), ensure_ascii=False)
                    ))
                    
                    # Respectful delay between article requests
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"Error parsing item: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error fetching Naver news page {page}: {e}")
            
        return news_items, should_stop

    def _is_within_one_hour(self, date_str: str) -> bool:
        """
        Check if the news was published within the last 1 hour.
        Naver formats: 'n분전', 'n시간전', '오전/오후 hh:mm', 'YYYY.MM.DD.'
        """
        if not date_str:
            return False
            
        # Clean up string
        date_str = date_str.replace(" ", "")
            
        if "분전" in date_str:
            minutes = int(re.search(r'(\d+)', date_str).group(1))
            return minutes <= 60
            
        if "시간전" in date_str:
            return False 
            
        if "오전" in date_str or "오후" in date_str or ":" in date_str:
            now = datetime.now()
            try:
                is_pm = "오후" in date_str
                match = re.search(r'(\d+):(\d+)', date_str)
                if not match: return False
                
                hour = int(match.group(1))
                if is_pm and hour != 12: hour += 12
                if not is_pm and hour == 12: hour = 0
                minute = int(match.group(2))
                
                published_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if published_time > now:
                    published_time -= timedelta(days=1)
                
                diff = now - published_time
                return diff.total_seconds() <= 3600
            except:
                return False

        return False

    def _fetch_metadata(self, url: str) -> dict:
        metadata = {"comment_count": 0, "reaction_count": 0, "reaction_detail": {}}
        try:
            # Extract officeId and articleId from URL
            # Format: .../001/0014620000 or ...oid=001&aid=0014620000
            match = re.search(r'article/(\d+)/(\d+)', url) or re.search(r'oid=(\d+)&aid=(\d+)', url)
            if not match:
                print(f"[Debug] Failed to extract IDs from: {url}")
                return metadata
            
            oid, aid = match.groups()
            # print(f"[Debug] Extracted OID: {oid}, AID: {aid} for {url}")
            
            # 1. Reaction API
            react_url = f"https://news.like.naver.com/v1/search/contents?suppress_response_codes=true&q=NEWS[ne_{oid}_{aid}]"
            react_res = requests.get(react_url, headers=self.headers, timeout=5)
            if react_res.status_code == 200:
                data = react_res.json()
                if data.get("contents"):
                    content = data["contents"][0]
                    metadata["reaction_count"] = content.get("reactionCount", 0)
                    # Detail map: like, cheer, congratulate, expect, surprised, sad, angry
                    # Mapping might vary, getting counts
                    reactions = content.get("reactions", [])
                    detail = {r["reactionType"]: r["count"] for r in reactions}
                    metadata["reaction_detail"] = detail

            # 2. Comment Count API
            # Note: objectId is news{oid},{aid}
            comment_url = f"https://apis.naver.com/commentBox/cbox/web_naver_list_jsonp.json?ticket=news&templateId=default_main&pool=cbox5&lang=ko&country=KR&objectId=news{oid},{aid}&pageSize=1"
            comment_res = requests.get(comment_url, headers=self.headers, timeout=5)
            if comment_res.status_code == 200:
                # Response is JSONP: _callback(json...)
                body = comment_res.text
                json_text = body[body.find("(") + 1 : body.rfind(")")]
                data = json.loads(json_text)
                if data.get("result"):
                    count_data = data["result"].get("count", {})
                    metadata["comment_count"] = count_data.get("total", 0)
                    
        except Exception as e:
            print(f"Error fetching metadata for {url}: {e}")
            
        return metadata

    def _fetch_full_content(self, url: str) -> str:
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            
            article_body = soup.select_one("#newsct_article") or soup.select_one("#articleBodyContents")
            
            if article_body:
                for s in article_body(["script", "style", "span.hidden", "div.article_footer"]):
                    s.extract()
                return article_body.get_text(separator="\n").strip()
        except Exception as e:
            print(f"Error fetching full content from {url}: {e}")
        return ""

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', text)
        text = re.sub(r'\(.*?\=.*?\)|\(.*?\/.*?\)|\<.*?\>', '', text)
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'ⓒ.*', '', text)
        text = re.sub(r'무단 전재 및 재배포 금지.*', '', text, flags=re.S)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
