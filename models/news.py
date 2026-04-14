from dataclasses import dataclass
from typing import Optional

@dataclass
class NewsItem:
    title: str
    snippet: str
    publisher: str
    published_at: str
    url: str
    full_content: str = ""

    def to_dict(self):
        return {
            "title": self.title,
            "snippet": self.snippet,
            "publisher": self.publisher,
            "published_at": self.published_at,
            "url": self.url,
            "full_content": self.full_content
        }
