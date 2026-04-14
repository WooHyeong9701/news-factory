import os
import requests
import json
import time
import google.generativeai as genai
from datetime import datetime

class ImageGenerator:
    def __init__(self):
        # GEMINI_API_KEY를 사용합니다. (.env에 추가 필요)
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def generate_news_images(self, topic: str, count: int = 3) -> list:
        """
        Gemini Imagen 3 모델을 사용하여 뉴스 주제에 맞는 이미지를 생성합니다.
        생성된 이미지는 web/static/gen_images 폴더에 저장됩니다.
        """
        print(f"🎨 Google AI (Imagen) 이미지 생성 중: {topic}")
        
        # 1. API 키가 없으면 샘플 이미지로 대체
        if not self.api_key:
            print("[!] GEMINI_API_KEY가 설정되지 않았습니다. 샘플 이미지를 사용합니다.")
            return [f"https://picsum.photos/seed/{topic[:5]}_{i}/1080/1080" for i in range(count)]

        image_urls = []
        try:
            # 2. Imagen 3 모델 선택
            # 참고: 지역 및 계정 권한에 따라 'imagen-3.0-generate-001' 또는 'imagen-2' 가능
            model = genai.GenerativeModel('imagen-3.0-generate-001')
            
            for i in range(count):
                # 프롬프트 구성 (인스타그램용 감성 및 고품질 강조)
                prompt = f"A professional, cinematic, high-quality digital art for a news headline about: '{topic}'. Instagram aesthetic, vivid colors, 4k. Image {i+1}."
                
                # 이미지 생성 호출 (SDK 지원여부에 따라 다를 수 있음)
                # 현재 SDK v0.7+ 에서 Imagen 지원
                response = model.generate_content(prompt)
                
                # 이미지 데이터 추출 및 파일 저장
                # Note: Imagen API는 이미지를 PIL 형식이나 바이트로 반환합니다.
                # 여기서는 파일로 저장하여 웹에서 서빙합니다.
                timestamp = int(time.time())
                filename = f"img_{timestamp}_{i}.png"
                filepath = os.path.join("web/static/gen_images", filename)
                
                # 생성된 이미지 저장 (SDK의 반환 방식에 맞춰 처리)
                # 만약 SDK에서 직접 지원하지 않는 지역인 경우 에러가 나므로 예외처리
                if hasattr(response, 'images') and len(response.images) > 0:
                    response.images[0].save(filepath)
                    image_urls.append(f"/static/gen_images/{filename}")
                else:
                    # Fallback: 생성 실패 시 픽섬 사용
                    print(f"[!] 이미지 {i} 생성 실패. Fallback 적용.")
                    image_urls.append(f"https://picsum.photos/seed/{topic[:5]}_{i}/1080/1080")
                
                time.sleep(1) # API 레이트 리밋 방지
                
        except Exception as e:
            print(f"[ERROR] Google AI 이미지 생성 도중 오류 발생: {e}")
            # 전체 실패 시 샘플 이미지 반환
            return [f"https://picsum.photos/seed/{topic[:5]}_{i}/1080/1080" for i in range(count)]
        
        return image_urls
