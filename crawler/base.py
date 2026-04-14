from abc import ABC, abstractmethod
from typing import List
from models.news import NewsItem

class BaseCrawler(ABC):
    @abstractmethod
    def fetch_news(self) -> List[NewsItem]:
        """Fetch news items from the source."""
        pass

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name of the news source."""
        pass
