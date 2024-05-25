FROM python:3.9-slim
WORKDIR /app
COPY . /app/
# COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# 포트 노출
EXPOSE 8080
# 애플리케이션 실행
CMD ["python", "app.py"]
