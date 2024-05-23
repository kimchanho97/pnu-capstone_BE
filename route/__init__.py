import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# 환경 변수 로드
load_dotenv()

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}}, expose_headers='Authorization')

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    from .models import User, Token, Project, Build, Deploy, Secret
    migrate.init_app(app, db)

    # 블루프린트와 서비스 로직 동적 로딩
    from .user.login import userBlueprint
    app.register_blueprint(userBlueprint, url_prefix='/user')

    from .project.routes import projectBlueprint
    app.register_blueprint(projectBlueprint, url_prefix='/project')

    # OPTIONS 요청에 대한 응답을 위한 미들웨어
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    return app