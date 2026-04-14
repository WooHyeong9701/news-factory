import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

class IssueClusterer:
    def __init__(self, threshold=0.75):
        self.threshold = threshold
        try:
            from konlpy.tag import Okt
            self.okt = Okt()
            self.has_konlpy = True
        except (ImportError, ModuleNotFoundError):
            print("Warning: KoNLPy not installed. Using fallback simple tokenizer.")
            self.has_konlpy = False
        except Exception as e:
            print(f"Warning: KoNLPy error ({e}). Using fallback simple tokenizer.")
            self.has_konlpy = False
        
        self.vectorizer = TfidfVectorizer(tokenizer=self._tokenize)
        
    def _tokenize(self, text):
        if not text:
            return []
        
        if self.has_konlpy:
            try:
                # Extract only nouns and ignore short words
                tokens = self.okt.nouns(text)
                return [t for t in tokens if len(t) > 1]
            except:
                pass
        
        # Fallback simple tokenizer (regex based words > 1 char)
        return [w for w in re.findall(r'[가-힣a-zA-Z0-9]{2,}', text)]

    def find_best_matching_issue(self, news_item, active_issues):
        """
        Compare new news item with existing active issues.
        Returns issue_id or None if no match found.
        """
        if not active_issues:
            return None

        # Prepare texts for comparison
        new_text = f"{news_item.title} {news_item.snippet}"
        issue_texts = [issue['representative_title'] for issue in active_issues]
        
        # Combine and vectorize
        all_texts = [new_text] + issue_texts
        try:
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)
        except ValueError:
            # Might happen if no tokens found
            return None

        # Calculate cosine similarity between the new item (index 0) and the rest
        cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
        
        max_idx = np.argmax(cosine_sim)
        max_sim = cosine_sim[0][max_idx]
        
        if max_sim >= self.threshold:
            return active_issues[max_idx]['id']
        
        return None
