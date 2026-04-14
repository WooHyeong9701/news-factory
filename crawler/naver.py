import requests
from bs4 import BeautifulSoup
from typing import List
from models.news import NewsItem
from crawler.base import BaseCrawler

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
            
            # Naver News Headline list selectors
            # Usually ul.type06_headline and ul.type06 contain the list items
            list_containers = soup.select("ul.type06_headline li") + soup.select("ul.type06 li")
            
            for item in list_containers:
                try:
                    # Selectors for Title
                    # If item has image, title is in the second dt tag. Otherwise first.
                    dt_tags = item.find_all("dt")
                    title_tag = dt_tags[-1].find("a")
                    title = title_tag.text.strip()
                    url = title_tag["href"]
                    
                    # Snippet
                    snippet_tag = item.find("span", class_="lede")
                    snippet = snippet_tag.text.strip() if snippet_tag else ""
                    
                    # Publisher
                    publisher_tag = item.find("span", class_="writing")
                    publisher = publisher_tag.text.strip() if publisher_tag else "Unknown"
                    
                    # Date/Time
                    date_tag = item.find("span", class_="date")
                    published_at = date_tag.text.strip() if date_tag else ""
                    
                    news_items.append(NewsItem(
                        title=title,
                        snippet=snippet,
                        publisher=publisher,
                        published_at=published_at,
                        url=url
                    ))
                except Exception as e:
                    # Individual item parsing might fail if structure varies slightly
                    continue
                    
        except Exception as e:
            print(f"Error fetching Naver news: {e}")
            
        return news_items
