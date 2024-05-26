import os
import requests

from .. import db
from ..models import User, Token


def getAccessTokenFromGithub(authCode):
    # GitHub 앱의 클라이언트 ID와 클라이언트 시크릿 설정
    clientId = os.getenv("GITHUB_CLIENT_ID")
    clientSecret = os.getenv("GITHUB_CLIENT_SECRET")
    redirectUri = "https://pitapat.ne.kr/callback"
    # redirectUri = 'http://localhost:3000/callback'
    # GitHub의 OAuth 서버 URL
    tokenUrl = 'https://github.com/login/oauth/access_token'

    # 액세스 토큰을 얻기 위한 POST 요청 데이터 준비
    data = {
        'client_id': clientId,
        'client_secret': clientSecret,
        'code': authCode,
        'redirect_uri': redirectUri,
    }

    # POST 요청을 위한 헤더 설정
    headers = {'Accept': 'application/json'}

    # 액세스 토큰을 받기 위해 POST 요청 수행
    response = requests.post(tokenUrl, data=data, headers=headers)
    print("github response = ", response.json())

    return response.json()


def getUserDataFromGithub(accessToken):
    return requests.get(
        "https://api.github.com/user",
        headers={
            "Authorization": f"Bearer {accessToken}",
            "Accept": "application/json"
        }
    )


def createUserAndInsertToken(login, nickname, avatarUrl, accessToken):
    try:
        # 1. DB에 User 정보 insert
        newUser = User(login=login, nickname=nickname, avatar_url=avatarUrl)
        db.session.add(newUser)
        db.session.flush()

        # 2. DB에 Token 정보 insert
        newToken = Token(user_id=newUser.id, access_token=accessToken)
        db.session.add(newToken)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e

    return newUser


def updateAccessToken(userId, accessToken):
    try:
        # 1. DB에 Token 정보 update
        token = Token.query.filter_by(user_id=userId).first()
        if token:
            token.access_token = accessToken
            db.session.commit()
        else:
            raise ValueError("Token not found for user_id: {}".format(userId))
    except Exception as e:
        db.session.rollback()
        raise e
    return
