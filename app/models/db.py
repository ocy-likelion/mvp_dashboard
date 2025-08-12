from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from app.config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_ENGINE_OPTIONS

db = SQLAlchemy()


def init_db(app):
    """데이터베이스 초기화"""
    db.init_app(app)

    # 엔진 생성
    engine = create_engine(SQLALCHEMY_DATABASE_URI, **SQLALCHEMY_ENGINE_OPTIONS)

    # 세션 팩토리 생성
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)

    return Session


def get_db_session():
    """데이터베이스 세션 반환"""
    from flask import current_app

    return current_app.db.session


# 기존 psycopg2 연결 함수 (마이그레이션 중 호환성을 위해 유지)
import psycopg2
from app.config import DATABASE_URL


def get_db_connection():
    """PostgreSQL 데이터베이스 연결 함수"""
    conn = psycopg2.connect(DATABASE_URL)
    return conn
