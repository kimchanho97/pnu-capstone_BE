FROM python:3.9
WORKDIR /work
COPY . /work/
RUN pip install -r requirements.txt
EXPOSE 8080
CMD ["python", "app.py"]
