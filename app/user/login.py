from flask import Blueprint, request, jsonify
from .utils import get_access_token, get_user_data_from_github, create_user_and_insert_token, update_token
from ..models import User

user_blueprint = Blueprint('user', __name__)

@user_blueprint.route('/login', methods=['POST'])
def github_login():
    auth_code = request.json.get('code')
    # print("auth_code: ", auth_code)

    if not auth_code:
        return jsonify({'error': 'Authorization code is required'}), 400

    # auth_code를 이용해 액세스 토큰을 받아옴
    response_json = get_access_token(auth_code)

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
            update_token(user.id, access_token)

        return jsonify({'access_token': access_token,
                        'login': login,
                        'nickname': nickname,
                        'avatar_url': avatar_url,
                        'id': user.id})
    else:
        error_message = response_json.get('error_description', 'Unknown error occurred.')
        return jsonify({'error': response_json.get('error', 'error'), 'error_description': error_message}), 400
