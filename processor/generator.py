import os
import google.generativeai as genai
import json

class ContentGenerator:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def generate_instagram_content(self, title: str, summary: str) -> dict:
        """
        Gemini AI를 사용하여 진중하고 전문적인 뉴스 제목 3개와 요약문을 생성합니다. (이모지 제외)
        """
        # API 키가 있으면 AI로 생성, 없으면 진중한 톤의 Fallback 사용
        if self.api_key:
            try:
                model = genai.GenerativeModel('gemini-1.5-pro')
                prompt = f"""
                다음 뉴스 제목과 요약을 바탕으로 인스타그램에 게시할 '진중하고 전문적인' 타이틀 1개와 요약문을 작성해줘.
                
                [뉴스 제목]: {title}
                [뉴스 요약]: {summary}
                
                [지시 사항]:
                1. 이모지(아이콘)를 절대로 사용하지 말 것.
                2. 자극적이거나 가벼운 말투 대신, 신문 사설이나 심층 보도 헤드라인 같은 격식 있는 말투를 사용할 것.
                3. 제목은 가장 적절한 '단 하나'의 후보만 줄 것.
                4. 요약문은 핵심 내용을 정중하게 전달할 것.
                5. 반드시 JSON 형식으로만 응답할 것: {{"title": "생성된제목", "summary": "요약문내용"}}
                """
                
                response = model.generate_content(prompt)
                json_str = response.text.replace('```json', '').replace('```', '').strip()
                result = json.loads(json_str)
                # 기존 UI 호환성을 위해 title을 titles 리스트로 변환 (또는 개별 처리)
                if "title" in result:
                    result["titles"] = [result["title"]]
                return result
                
            except Exception as e:
                print(f"[ERROR] Gemini 콘텐츠 생성 실패: {e}")

        # Fallback (AI 실패 시 또는 키 없을 때) - 진중하고 격식 있는 톤
        titles = [
            f"[심층보고] {title}",
            f"{title} : 실시간 주요 현황 보고",
            f"주요 이슈 분석: {title}"
        ]
        
        ig_summary = (
            f"주요 뉴스 보고\n\n"
            f"{summary}\n\n"
            "본 보고서는 실시간 데이터를 바탕으로 작성되었습니다.\n\n"
            "#사회이슈 #심층보도 #뉴스분석"
        )
        
        return {
            "titles": titles,
            "summary": ig_summary
        }
