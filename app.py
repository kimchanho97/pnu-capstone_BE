from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=8080)  # 서버 시작, 포트 8080에서 리스닝
