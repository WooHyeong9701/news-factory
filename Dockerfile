# 1. Python 3.9 슬림 이미지를 기반으로 시작
FROM python:3.9-slim

# 2. 시스템 필수 라이브러리 및 Java(KoNLPy용) 설치
RUN apt-get update && apt-get install -y \
    openjdk-17-jdk-headless \
    g++ \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# 3. 환경 변수 설정 (Java 경로 및 Python 경로)
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PYTHONPATH=/app

# 4. 작업 디렉토리 설정
WORKDIR /app

# 5. 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# python-multipart는 FastAPI 폼 데이터를 위해 필수
RUN pip install python-multipart

# 6. 소스 코드 복사
COPY . .

# 7. 데이터베이스 초기화 및 서버 실행
# migrate.py를 먼저 실행하여 테이블을 생성한 뒤 서버를 켭니다.
CMD ["sh", "-c", "python3 migrate.py && python3 web/app.py"]
