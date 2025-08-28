from decouple import config

# PostgreSQL 데이터베이스 연결 설정
DATABASE_URL = config("DATABASE_URL", default=None)

# SQLAlchemy 설정
SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": config("DB_POOL_SIZE", default=10, cast=int),
    "pool_recycle": config("DB_POOL_RECYCLE", default=3600, cast=int),
    "pool_pre_ping": config("DB_POOL_PRE_PING", default=True, cast=bool),
    "max_overflow": config("DB_MAX_OVERFLOW", default=20, cast=int),
}

# 서버 포트 설정
PORT = config("PORT", default=10000, cast=int)

# Flask 설정
SECRET_KEY = config("SECRET_KEY", default="dev-secret-key-change-in-production")
DEBUG = config("DEBUG", default=False, cast=bool)
