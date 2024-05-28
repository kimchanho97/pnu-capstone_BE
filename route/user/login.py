from flask import Blueprint, request, jsonify, make_response
from .utils import getAccessTokenFromGithub, getUserDataFromGithub, createUserAndInsertToken, updateAccessToken
from ..models import User

userBlueprint = Blueprint('user', __name__)

@userBlueprint.route('/login', methods=['POST'])
def githubLogin():
    authCode = request.json.get('code')
    if not authCode:
        return jsonify({'error': {'message': 'Authorization code is required',
                                  'status': 400}}), 400

    accessToken = getAccessTokenFromGithub(authCode)
    userData = getUserDataFromGithub(accessToken).json()

    login = userData["login"]
    nickname = userData["name"]
    avatarUrl = userData["avatar_url"]

    user = User.query.filter_by(login=login).first()
    if user is None:
        user = createUserAndInsertToken(login, nickname, avatarUrl, accessToken)
    else:
        updateAccessToken(user.id, accessToken)

    responseData = jsonify({
                    'login': login,
                    'nickname': nickname,
                    'avatarUrl': avatarUrl,
                    'id': user.id})
    response = make_response(responseData)
    response.headers['Authorization'] = f'Bearer {accessToken}'
    return response

