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
    CORS(app)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    from .models import User, Token
    migrate.init_app(app, db)

    # 블루프린트와 서비스 로직 동적 로딩
    from .user.login import user_blueprint
    app.register_blueprint(user_blueprint, url_prefix='/user')

    return app