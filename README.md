# News Factory - Python News Crawler

네이버 뉴스의 실시간 속보를 크롤링하여 SQLite 데이터베이스에 저장하는 프로그램입니다.

## 주요 특징
- **확장성**: `BaseCrawler` 추상 클래스를 기반으로 설계되어 새로운 타겟(다음, 구글 등)을 쉽게 추가할 수 있습니다.
- **Deduplication**: URL을 고유 키로 사용하여 데이터 중복 저장을 방지합니다.
- **실시간성**: Search API 대신 BeautifulSoup을 사용하여 랭킹/속보 페이지를 직접 파싱하므로 더 빠른 업데이트를 반영할 수 있습니다.

## 설치 방법
```bash
python3 -m pip install -r requirements.txt
```

## 실행 방법
```bash
python3 main.py
```

## 프로젝트 구조
- `crawler/`: 크롤러 구현체 폴더
    - `base.py`: 모든 크롤러가 상속받아야 할 기본 인터페이스
    - `naver.py`: 네이버 뉴스 크롤링 로직 (sid1=001 속보 대상)
- `database/`: 데이터베이스 관련 로직
    - `sqlite_db.py`: SQLite 테이블 생성 및 CRUD
- `models/`: 데이터 구조 정의
    - `news.py`: 뉴스 정보를 담는 Data Class
- `main.py`: 실행 진입점

## 데이터 정보
저장되는 정보는 다음과 같습니다:
- 제목 (Title)
- 본문 요약 (Snippet)
- 언론사명 (Publisher)
- 발생 시각 (Published At)
- URL (Unique Key)
