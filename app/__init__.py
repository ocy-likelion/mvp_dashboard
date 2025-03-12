from flask import Flask
from flask_cors import CORS
from flasgger import Swagger
import logging
from app.config import Config

# 로깅 설정
logging.basicConfig(level=logging.ERROR)

def create_app():
    app = Flask(__name__, template_folder='templates')
    
    # 설정 적용
    app.config.from_object(Config)
    
    # CORS 설정
    CORS(app, supports_credentials=True)
    
    # Swagger 초기화
    Swagger(app)
    
    # 블루프린트 등록
    from app.routes import auth, admin, tasks, irregular_tasks, notices, issues, training, unchecked
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(tasks.bp)
    app.register_blueprint(irregular_tasks.bp)
    app.register_blueprint(notices.bp)
    app.register_blueprint(issues.bp)
    app.register_blueprint(training.bp)
    app.register_blueprint(unchecked.bp)
    
    return app 