import requests
from bs4 import BeautifulSoup
from typing import List
from models.news import NewsItem
from crawler.base import BaseCrawler

import re

class NaverNewsCrawler(BaseCrawler):
    def __init__(self):
        self.url = "https://news.naver.com/main/list.naver?mode=LSD&mid=sec&sid1=001"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    @property
    def source_name(self) -> str:
        return "Naver"

    def fetch_news(self) -> List[NewsItem]:
        news_items = []
        try:
            response = requests.get(self.url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "lxml")
            list_containers = soup.select("ul.type06_headline li") + soup.select("ul.type06 li")
            
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
                    published_at = date_tag.text.strip() if date_tag else ""
                    
                    # Deep Crawling: Fetch full content
                    full_content = self._fetch_full_content(url)
                    cleaned_content = self._clean_text(full_content)
                    
                    news_items.append(NewsItem(
                        title=title,
                        snippet=original_snippet, # Will be replaced by summary in main.py
                        publisher=publisher,
                        published_at=published_at,
                        url=url,
                        full_content=cleaned_content
                    ))
                except Exception as e:
                    print(f"Error parsing item: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error fetching Naver news: {e}")
            
        return news_items

    def _fetch_full_content(self, url: str) -> str:
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            
            # Target Naver News article body
            article_body = soup.select_one("#newsct_article") or soup.select_one("#articleBodyContents")
            
            if article_body:
                # Remove script and style elements
                for s in article_body(["script", "style", "span.hidden", "div.article_footer"]):
                    s.extract()
                return article_body.get_text(separator="\n").strip()
        except Exception as e:
            print(f"Error fetching full content from {url}: {e}")
        return ""

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        # Remove emails
        text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', text)
        # Remove typical copyright/reporter markers
        text = re.sub(r'\(.*?\=.*?\)|\(.*?\/.*?\)|\<.*?\>', '', text)
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'ⓒ.*', '', text)
        text = re.sub(r'무단 전재 및 재배포 금지.*', '', text, flags=re.S)
        # Clean up whitespaces
        text = re.sub(r'\s+', ' ', text).strip()
        return text
