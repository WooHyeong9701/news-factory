import os

class Summarizer:
    def summarize(self, text: str) -> str:
        if not text:
            return ""
        
        # Simple extraction-based summary as fallback
        sentences = text.split(". ")
        if len(sentences) <= 3:
            return text
        
        # Return first 3 sentences
        return ". ".join(sentences[:3]) + "."

# Potential integration for Gemini/OpenAI
class AISummarizer(Summarizer):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("AI_API_KEY")

    def summarize(self, text: str) -> str:
        if not self.api_key:
            return super().summarize(text)
        
        # Placeholder for AI API call
        # print("Calling AI API for summarization...")
        return super().summarize(text) # Fallback for now
