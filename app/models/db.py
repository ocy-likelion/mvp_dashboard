import psycopg2
import os

def get_db_connection():
    """PostgreSQL 데이터베이스 연결 함수"""
    # 직접 환경 변수에서 DATABASE_URL 값을 읽습니다
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        DATABASE_URL = "postgresql://cysss:QJxyP6VuLMAZykzMyeRtO3QJUGMf0aWA@dpg-cuim9pogph6c73acoj0g-a/mvp_dashboard"
    
    conn = psycopg2.connect(DATABASE_URL)
    return conn