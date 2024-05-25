FROM python:3.9-slim
WORKDIR /work
COPY . /work/
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8080
CMD ["python", "app.py"]
# test
