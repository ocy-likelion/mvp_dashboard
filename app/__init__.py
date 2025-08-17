import logging
import sys
from flask import Flask
from flask_cors import CORS
from flasgger import Swagger
from datetime import timedelta
from app.models.db import init_db
from app.config import (
    SECRET_KEY,
    DEBUG,
    SQLALCHEMY_DATABASE_URI,
    SQLALCHEMY_TRACK_MODIFICATIONS,
    SQLALCHEMY_ENGINE_OPTIONS,
)

# 전역 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def create_app():
    app = Flask(__name__, template_folder="templates")
    logger = logging.getLogger(__name__)
    logger.info("애플리케이션 시작")

    # Flask 기본 설정
    app.secret_key = SECRET_KEY
    app.debug = DEBUG

    # SQLAlchemy 설정
    app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = SQLALCHEMY_TRACK_MODIFICATIONS
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = SQLALCHEMY_ENGINE_OPTIONS

    # 데이터베이스 초기화
    init_db(app)

    # 세션 설정 강화
    app.config.update(
        SESSION_COOKIE_SECURE=True,  # HTTPS에서만 쿠키 전송
        SESSION_COOKIE_HTTPONLY=True,  # JavaScript에서 쿠키 접근 방지
        SESSION_COOKIE_SAMESITE="Lax",  # CSRF 공격 방지
        PERMANENT_SESSION_LIFETIME=timedelta(
            hours=12
        ),  # 세션 유효 시간 12시간으로 설정
    )

    CORS(app, supports_credentials=True)  # CORS 설정 강화 (세션 쿠키 허용)

    app.config["SWAGGER"] = {
        "title": "업무 관리 대시보드 API",
        "uiversion": 3,  # 최신 Swagger UI 사용
        "specs_route": "/apidocs",  # 끝의 슬래시(/) 제거
    }
    Swagger(app)  # Flasgger 초기화

    # 라우터 등록
    from app.routes import register_routes

    register_routes(app)

    return app
