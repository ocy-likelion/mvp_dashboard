import psycopg2
from app.config import Config

def get_db_connection():
    """데이터베이스 연결을 생성하고 반환합니다."""
    conn = psycopg2.connect(Config.DATABASE_URL)
    return conn 