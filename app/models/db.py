import psycopg2
from app.config import DATABASE_URL


def get_db_connection():
    """PostgreSQL 데이터베이스 연결 함수"""
    conn = psycopg2.connect(DATABASE_URL)
    return conn
