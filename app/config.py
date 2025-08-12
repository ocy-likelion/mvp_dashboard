import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# PostgreSQL 데이터베이스 연결 설정
DATABASE_URL = os.getenv("DATABASE_URL")

# SQLAlchemy 설정
SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 10,
    "pool_recycle": 3600,
    "pool_pre_ping": True,
    "max_overflow": 20,
}

# 서버 포트 설정
PORT = int(os.getenv("PORT", 10000))  # 기본값을 10000으로 설정
