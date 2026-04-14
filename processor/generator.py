import json

class ContentGenerator:
    def __init__(self):
        pass

    def generate_instagram_content(self, title: str, summary: str) -> dict:
        """
        Generates 3 title candidates and 1 Instagram-style summary.
        In a production environment, this would call an LLM (Gemini/GPT).
        """
        # 1. Generate 3 catchier titles for IG
        titles = [
            f"📢 {title}",
            f"🔥 지금 난리난 뉴스: {title}",
            f"👀 이거 보셨나요? {title}"
        ]
        
        # 2. Reformat summary with emojis for IG
        ig_summary = f"✨ 뉴스 요약 도착! ✨\n\n"
        ig_summary += f"📍 {summary}\n\n"
        ig_summary += "더 자세한 내용은 웹사이트에서 확인하세요! 🚀\n\n"
        ig_summary += "#뉴스 #이슈 #실시간 #인스타뉴스"
        
        return {
            "titles": titles,
            "summary": ig_summary
        }
