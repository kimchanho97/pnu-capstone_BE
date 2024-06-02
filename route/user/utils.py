import os
import requests

from .. import db
from ..models import User, Token
from sqlalchemy.exc import SQLAlchemyError


def getAccessTokenFromGithub(authCode):
    clientId = os.getenv("GITHUB_CLIENT_ID")
    clientSecret = os.getenv("GITHUB_CLIENT_SECRET")
    # redirectUri = "https://pitapat.ne.kr/callback"
    redirectUri = 'http://localhost:3000/callback'
    tokenUrl = 'https://github.com/login/oauth/access_token'
    data = {
        'client_id': clientId,
        'client_secret': clientSecret,
        'code': authCode,
        'redirect_uri': redirectUri,
    }
    headers = {'Accept': 'application/json'}
    response = requests.post(tokenUrl, data=data, headers=headers)
    return response.json()['access_token']


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
        newUser = User(login=login, nickname=nickname, avatar_url=avatarUrl)
        db.session.add(newUser)
        db.session.flush()

        newToken = Token(user_id=newUser.id, access_token=accessToken)
        db.session.add(newToken)
        db.session.commit()
        return newUser
    except SQLAlchemyError as e:
        raise e


def updateAccessToken(userId, accessToken):
    try:
        token = Token.query.filter_by(user_id=userId).first()
        token.access_token = accessToken
        db.session.commit()

    except SQLAlchemyError as e:
        raise e