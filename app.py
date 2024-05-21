from route import create_app
from route.celery_utils import make_celery

app = create_app()
celery = make_celery(app)

if __name__ == '__main__':
    app.run(debug=True, port=8080)  # 서버 시작, 포트 8080에서 리스닝

