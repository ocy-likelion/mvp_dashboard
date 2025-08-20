from typing import Dict, List

from .base import Serializer
from app.schemas import (
    unchecked_description_schema,
    unchecked_descriptions_schema,
    unchecked_comment_schema,
    unchecked_comments_schema,
    unchecked_description_create_schema,
    unchecked_comment_create_schema,
    unchecked_resolve_schema,
    irregular_task_create_schema,
)


class UncheckedSerializer:
    """미해결 항목 관련 직렬화 함수들"""

    @staticmethod
    def deserialize_unchecked_description_create(data: Dict) -> Dict:
        """미해결 항목 생성 데이터 역직렬화"""
        return Serializer.deserialize(data, unchecked_description_create_schema)

    @staticmethod
    def deserialize_unchecked_comment_create(data: Dict) -> Dict:
        """미해결 댓글 생성 데이터 역직렬화"""
        return Serializer.deserialize(data, unchecked_comment_create_schema)

    @staticmethod
    def deserialize_unchecked_resolve(data: Dict) -> Dict:
        """미해결 항목 해결 데이터 역직렬화"""
        return Serializer.deserialize(data, unchecked_resolve_schema)

    @staticmethod
    def deserialize_irregular_task_create(data: Dict) -> Dict:
        """불규칙 업무 생성 데이터 역직렬화"""
        return Serializer.deserialize(data, irregular_task_create_schema)
