"""
Database utilities and context managers
"""

from contextlib import contextmanager
from app.models.db import get_db_session
import logging

logger = logging.getLogger(__name__)


@contextmanager
def db_session():
    """
    데이터베이스 세션 컨텍스트 매니저
    자동으로 커밋/롤백/클로즈를 처리합니다.

    사용법:
        with db_session() as session:
            # 데이터베이스 작업 수행
            result = session.query(Model).all()
            # 성공 시 자동 커밋

    예외 발생 시 자동으로 롤백됩니다.
    """
    session = get_db_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database transaction failed: {str(e)}")
        raise
    finally:
        session.close()


@contextmanager
def db_session_read_only():
    """
    읽기 전용 데이터베이스 세션 컨텍스트 매니저
    커밋하지 않고 세션만 관리합니다.

    사용법:
        with db_session_read_only() as session:
            # 읽기 전용 작업
            result = session.query(Model).all()
    """
    session = get_db_session()
    try:
        yield session
    finally:
        session.close()
