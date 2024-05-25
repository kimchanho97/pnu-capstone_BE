# 베이스 이미지 설정
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 필요 패키지 복사 및 설치
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 소스 코드 복사
COPY . .

# 환경 변수 로드
COPY .env .env

# 포트 노출
EXPOSE 8080

# 애플리케이션 실행
CMD ["python", "app.py"]
