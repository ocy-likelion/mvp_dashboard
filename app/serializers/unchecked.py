from typing import Dict, List

from .base import Serializer
from app.schemas import (
    unchecked_description_schema,
    unchecked_descriptions_schema,
    unchecked_comment_schema,
    unchecked_comments_schema,
    unchecked_comment_filter_schema,
    unchecked_description_create_schema,
    unchecked_comment_create_schema,
    unchecked_resolve_schema,
    irregular_task_create_schema,
)


class UncheckedSerializer:
    """미해결 항목 관련 직렬화 함수들"""

    @staticmethod
    def serialize_unchecked_description(unchecked_item) -> Dict:
        """단일 미해결 항목 직렬화"""
        return Serializer.serialize(unchecked_item, unchecked_description_schema)

    @staticmethod
    def serialize_unchecked_descriptions(unchecked_items: List) -> List[Dict]:
        """여러 미해결 항목 직렬화"""
        return Serializer.serialize(unchecked_items, unchecked_descriptions_schema, many=True)

    @staticmethod
    def serialize_unchecked_comment(unchecked_comment) -> Dict:
        """단일 미해결 댓글 직렬화"""
        return Serializer.serialize(unchecked_comment, unchecked_comment_schema)

    @staticmethod
    def serialize_unchecked_comments(unchecked_comments: List) -> List[Dict]:
        """여러 미해결 댓글 직렬화"""
        return Serializer.serialize(unchecked_comments, unchecked_comments_schema, many=True)

    @staticmethod
    def deserialize_unchecked_comment_get(query_params: Dict) -> Dict:
        """미해결 댓글 조회 쿼리 파라미터 검증 및 변환"""
        return Serializer.deserialize(query_params, unchecked_comment_filter_schema)

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
