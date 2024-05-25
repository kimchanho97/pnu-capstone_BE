FROM python:3.9
WORKDIR /work
COPY . /work/
RUN pip install -r requirements.txt
EXPOSE 8080
CMD ["sh", "-c", "flask db upgrade && flask run --host=0.0.0.0 --port=8080"]
