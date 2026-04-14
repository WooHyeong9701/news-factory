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
    comment_count: int = 0
    reaction_count: int = 0
    reaction_detail: str = "{}" 
    issue_id: Optional[int] = None

    def to_dict(self):
        return {
            "title": self.title,
            "snippet": self.snippet,
            "publisher": self.publisher,
            "published_at": self.published_at,
            "url": self.url,
            "full_content": self.full_content,
            "comment_count": self.comment_count,
            "reaction_count": self.reaction_count,
            "reaction_detail": self.reaction_detail,
            "issue_id": self.issue_id
        }
