from flask import Flask, request, jsonify
import requests, os
from dotenv import load_dotenv
from flask_cors import CORS  # CORS 모듈 임포트

load_dotenv()  # .env 파일에서 환경 변수 로드

app = Flask(__name__)
CORS(app)  # 모든 도메인에서의 CORS 요청을 허용


@app.route('/user/github', methods=['POST'])
def github_login():
    # 요청에서 인증 코드 추출
    auth_code = request.json.get('code')
    # print("auth_code: ", auth_code)

    if not auth_code:
        return jsonify({'error': 'Authorization code is required'}), 400

    # GitHub 앱의 클라이언트 ID와 클라이언트 시크릿 설정
    client_id = os.getenv("GITHUB_CLIENT_ID")
    client_secret = os.getenv("GITHUB_CLIENT_SECRET")
    redirect_uri = 'http://localhost:3000/callback'

    # GitHub의 OAuth 서버 URL
    token_url = 'https://github.com/login/oauth/access_token'

    # 액세스 토큰을 얻기 위한 POST 요청 데이터 준비
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': auth_code,
        'redirect_uri': redirect_uri
    }

    # POST 요청을 위한 헤더 설정
    headers = {'Accept': 'application/json'}

    # 액세스 토큰을 받기 위해 POST 요청 수행
    response = requests.post(token_url, data=data, headers=headers)
    print("response status code = ", response.status_code)
    print("github response = ", response.json())

    # 요청이 성공적이었는지 확인
    response_json = response.json()  # JSON 형태로 응답을 받음

    # GitHub API 응답 내용을 확인하여 에러가 있는지 검사
    if 'access_token' in response_json:
        # 액세스 토큰이 있는 경우, 사용자 정보를 받아오기 위해 GitHub API에 GET 요청
        access_token = response_json['access_token']
        user_data = requests.get(
            "https://api.github.com/user",
            headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
            }
        )
        user_email = requests.get(
            "https://api.github.com/user/emails",
            headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
            }
        )
        print("user_data = ", user_data.json())
        print("user_email = ", user_email.json())
        return jsonify({'access_token': response_json['access_token']})
    else:
        error_message = response_json.get('error_description', 'Unknown error occurred.')
        return jsonify({'error': response_json.get('error', 'error'), 'error_description': error_message}), 400

if __name__ == '__main__':
    app.run(debug=True, port=8080)  # 서버 시작, 포트 8080에서 리스닝
