from flask import Blueprint, request, jsonify, make_response
from .utils import getAccessTokenFromGithub, getUserDataFromGithub, createUserAndInsertToken, updateAccessToken
from ..models import User

userBlueprint = Blueprint('user', __name__)

@userBlueprint.route('/login', methods=['POST'])
def githubLogin():
    authCode = request.json.get('code')
    # print("authCode: ", authCode)

    if not authCode:
        return jsonify({'error': {'message': 'Authorization code is required',
                                  'status': 400}}), 400

    # auth_code를 이용해 액세스 토큰을 받아옴
    responseJson = getAccessTokenFromGithub(authCode)

    if 'access_token' in responseJson:
        accessToken = responseJson['access_token']
        userData = getUserDataFromGithub(accessToken).json()

        login = userData["login"]
        nickname = userData["name"]
        avatarUrl = userData["avatar_url"]

        # DB에 User 정보가 있는지 확인
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

        # 응답 객체 생성 및 헤더 설정
        response = make_response(responseData)
        response.headers['Authorization'] = f'Bearer {accessToken}'

        return response
    else:
        errorMessage = responseJson.get('error_description', 'Unknown error occurred.')
        return jsonify({'error': {'message': errorMessage,
                                  'status': 400}}), 400
