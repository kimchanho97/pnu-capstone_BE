import os

from flask import jsonify
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_sse import sse

# 환경 변수 로드
load_dotenv()

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}}, expose_headers='Authorization')

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config["REDIS_URL"] = os.getenv('REDIS_URL')

    db.init_app(app)
    from .models import User, Token, Project, Build, Deploy, Secret
    migrate.init_app(app, db)

    # 블루프린트와 서비스 로직 동적 로딩
    from .user.login import userBlueprint
    app.register_blueprint(userBlueprint, url_prefix='/user')

    from .project.routes import projectBlueprint
    app.register_blueprint(projectBlueprint, url_prefix='/project')

    # Add CORS for sse blueprint
    cors = CORS()
    cors.init_app(sse, resources={r"/stream/*": {"origins": "*"}})
    app.register_blueprint(sse, url_prefix='/stream')

    # 데이터베이스 테이블 정보를 반환하는 엔드포인트
    @app.route('/tables', methods=['GET'])
    def get_tables():
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = {}
        for table_name in inspector.get_table_names():
            columns = []
            for column in inspector.get_columns(table_name):
                columns.append({
                    'name': column['name'],
                    'type': str(column['type'])
                })
            tables[table_name] = columns
        return jsonify(tables)


    # OPTIONS 요청에 대한 응답을 위한 미들웨어
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    return app
