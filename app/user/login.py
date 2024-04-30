from flask import Blueprint, request, jsonify, make_response
from .utils import get_access_token_from_github, get_user_data_from_github, create_user_and_insert_token, update_access_token
from ..models import User

user_blueprint = Blueprint('user', __name__)

@user_blueprint.route('/login', methods=['POST'])
def github_login():
    auth_code = request.json.get('code')
    # print("auth_code: ", auth_code)

    if not auth_code:
        return jsonify({'error': 'Authorization code is required'}), 400

    # auth_code를 이용해 액세스 토큰을 받아옴
    response_json = get_access_token_from_github(auth_code)

    if 'access_token' in response_json:
        access_token = response_json['access_token']
        user_data = get_user_data_from_github(access_token).json()

        login = user_data["login"]
        nickname = user_data["name"]
        avatar_url = user_data["avatar_url"]

        # DB에 User 정보가 있는지 확인
        user = User.query.filter_by(login=login).first()
        if user is None:
            user = create_user_and_insert_token(login, nickname, avatar_url, access_token)
        else:
            update_access_token(user.id, access_token)

        response_data = jsonify({
                        'login': login,
                        'nickname': nickname,
                        'avatar_url': avatar_url,
                        'id': user.id})

        # 응답 객체 생성 및 헤더 설정
        response = make_response(response_data)
        response.headers['Authorization'] = f'Bearer {access_token}'

        return response
    else:
        error_message = response_json.get('error_description', 'Unknown error occurred.')
        return jsonify({'error': response_json.get('error', 'error'), 'error_description': error_message}), 400
