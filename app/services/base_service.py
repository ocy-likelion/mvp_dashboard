"""
Base service class for common functionality
"""

from typing import Any
from sqlalchemy.orm import Session


class BaseService:
    """Base service class with common methods"""

    @staticmethod
    def validate_db_session(session: Session) -> None:
        """Validate that database session is active and not closed"""
        if not session.is_active:
            raise ValueError("Database session is not active")
        if session.bind is None:
            raise ValueError("Database session has no bind")

    @staticmethod
    def safe_get_by_id(
        session: Session,
        model_class: Any,
        item_id: int,
        error_message: str = "항목을 찾을 수 없습니다.",
    ):
        """Safely get an item by ID with error handling"""
        BaseService.validate_db_session(session)
        item = session.query(model_class).filter(model_class.id == item_id).first()
        if not item:
            raise ValueError(error_message)
        return item

    @staticmethod
    def flush_and_get_id(session: Session, instance: Any) -> int:
        """Add instance to session, flush and return ID"""
        session.add(instance)
        session.flush()
        return instance.id
