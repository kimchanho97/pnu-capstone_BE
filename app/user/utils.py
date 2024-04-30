import os
import requests

from .. import db
from ..models import User, Token


def get_access_token(auth_code):
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

    return response.json()


def get_user_data_from_github(access_token):
    return requests.get(
        "https://api.github.com/user",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
    )


def create_user_and_insert_token(login, nickname, avatar_url, access_token):
    # 1. DB에 User 정보 insert
    new_user = User(login=login, nickname=nickname, avatar_url=avatar_url)
    db.session.add(new_user)
    db.session.commit()

    # 2. DB에 Token 정보 insert
    new_token = Token(user_id=new_user.id, access_token=access_token)
    db.session.add(new_token)
    db.session.commit()
    return new_user


def update_token(user_id, access_token):
    # 1. DB에 Token 정보 update
    token = Token.query.filter_by(user_id=user_id).first()
    token.access_token = access_token
    db.session.commit()
    return
