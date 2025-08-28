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

    # Swagger 설정 개선
    app.config["SWAGGER"] = {
        "title": "업무 관리 대시보드 API",
        "uiversion": 3,
        "specs_route": "/apidocs",
        "specs": [
            {
                "endpoint": "apispec_1",
                "route": "/apispec_1.json",
                "rule_filter": lambda rule: True,  # 모든 라우트 포함
                "model_filter": lambda tag: True,  # 모든 모델 포함
            }
        ],
        "swagger_ui_bundle_js": "//unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        "swagger_ui_standalone_preset_js": "//unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js",
        "jquery_js": "//unpkg.com/jquery@2.2.4/dist/jquery.min.js",
        "swagger_ui_css": "//unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css",
        "specs_route": "/apidocs/",
        "info": {
            "title": "업무 관리 대시보드 API",
            "description": """
            ## 업무 관리 대시보드 API 문서
            
            이 API는 교육 과정 관리, 출퇴근 기록, 공지사항, 이슈 관리 등의 기능을 제공합니다.
            
            ### 주요 기능
            - **인증 관리**: 로그인/로그아웃, 사용자 정보 조회
            - **공지사항**: 공지사항 CRUD, 읽음 표시, 페이지네이션 및 필터링
            - **업무 체크리스트**: 정기/비정기 업무 체크리스트 관리
            - **이슈 관리**: 이슈 등록, 댓글, 해결 처리
            - **출퇴근 기록**: 출퇴근 시간 기록 및 조회, 월별 필터링 및 페이지네이션
            - **훈련 과정**: 훈련 과정 정보 관리
            - **관리자 기능**: 체크율 통계, 미체크 항목 관리
            - **알림**: Slack 연동 알림 시스템
            
            ### 페이지네이션
            목록 조회 API는 페이지네이션을 지원합니다:
            - `page`: 페이지 번호 (기본값: 1)
            - `per_page`: 페이지당 항목 수 (기본값: 10, 최대: 100)
            
            페이지네이션 응답 형식:
            ```json
            {
                "success": true,
                "message": "조회 성공",
                "data": {
                    "items": [...],
                    "pagination": {
                        "page": 1,
                        "per_page": 10,
                        "total_count": 25,
                        "total_pages": 3,
                        "has_next": true,
                        "has_prev": false
                    }
                },
                "status_code": 200
            }
            ```
            
            ### 필터링 기능
            - **공지사항**: 유형별 필터링, 제목/내용 검색
            - **출퇴근 기록**: 년도/월별 필터링, 강사별 필터링, 훈련과정별 필터링
            
            ### 인증
            대부분의 API는 세션 기반 인증을 사용합니다. 로그인 후 세션 쿠키가 자동으로 설정됩니다.
            
            ### 응답 형식
            모든 API는 다음과 같은 통일된 응답 형식을 사용합니다:
            ```json
            {
                "success": true,
                "message": "성공 메시지",
                "data": { ... },
                "status_code": 200
            }
            ```
            
            ### 에러 처리
            에러 발생 시 다음과 같은 형식으로 응답합니다:
            ```json
            {
                "success": false,
                "message": "에러 메시지",
                "status_code": 400
            }
            ```
            """,
            "version": "1.0.0",
            "contact": {
                "name": "API Support",
                "email": "support@example.com"
            },
            "license": {
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT"
            }
        },
        "securityDefinitions": {
            "sessionAuth": {
                "type": "apiKey",
                "name": "session",
                "in": "cookie",
                "description": "세션 기반 인증 (로그인 후 자동 설정)"
            }
        },
        "security": [
            {
                "sessionAuth": []
            }
        ],
        "consumes": ["application/json"],
        "produces": ["application/json"],
        "tags": [
            {
                "name": "Authentication",
                "description": "사용자 인증 관련 API"
            },
            {
                "name": "Notices", 
                "description": "공지사항 관리 API (페이지네이션 및 필터링 지원)"
            },
            {
                "name": "Tasks",
                "description": "업무 체크리스트 관리 API"
            },
            {
                "name": "Irregular Tasks",
                "description": "비정기 업무 체크리스트 API"
            },
            {
                "name": "Issues",
                "description": "이슈 관리 API"
            },
            {
                "name": "Attendance",
                "description": "출퇴근 기록 관리 API (월별 필터링 및 페이지네이션 지원)"
            },
            {
                "name": "Training Info",
                "description": "훈련 과정 정보 관리 API"
            },
            {
                "name": "Unchecked Descriptions",
                "description": "미체크 항목 설명 관리 API"
            },
            {
                "name": "Unchecked Comments",
                "description": "미체크 항목 댓글 관리 API"
            },
            {
                "name": "Admin",
                "description": "관리자 기능 API"
            },
            {
                "name": "Notifications",
                "description": "알림 관리 API"
            },
            {
                "name": "Views",
                "description": "페이지 뷰 API"
            },
            {
                "name": "System",
                "description": "시스템 관련 API"
            }
        ]
    }
    Swagger(app)  # Flasgger 초기화

    # 라우터 등록
    from app.routes import register_routes

    register_routes(app)

    return app
