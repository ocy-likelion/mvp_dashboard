from typing import Dict, List

from .base import Serializer
from app.schemas import (
    issue_schema,
    issues_schema,
    issue_comment_schema,
    issue_comments_schema,
    issue_create_schema,
    issue_comment_create_schema,
    issue_resolve_schema,
    issue_comment_filter_schema,
)


class IssueSerializer:
    """이슈 관련 직렬화 함수들"""

    @staticmethod
    def serialize_issue(issue) -> Dict:
        """단일 이슈 직렬화"""
        return Serializer.serialize(issue, issue_schema)

    @staticmethod
    def serialize_issues(issues: List) -> List[Dict]:
        """여러 이슈 직렬화"""
        return Serializer.serialize(issues, issues_schema, many=True)

    @staticmethod
    def serialize_issue_comment(comment) -> Dict:
        """단일 이슈 댓글 직렬화"""
        return Serializer.serialize(comment, issue_comment_schema)

    @staticmethod
    def serialize_issue_comments(comments: List) -> List[Dict]:
        """여러 이슈 댓글 직렬화"""
        return Serializer.serialize(comments, issue_comments_schema, many=True)

    @staticmethod
    def deserialize_issue_comment_get(query_params: Dict) -> Dict:
        """이슈 댓글 조회 쿼리 파라미터 검증 및 변환"""
        return Serializer.deserialize(query_params, issue_comment_filter_schema)

    @staticmethod
    def deserialize_issue_create(data: Dict) -> Dict:
        """이슈 생성 데이터 역직렬화"""
        return Serializer.deserialize(data, issue_create_schema)

    @staticmethod
    def deserialize_issue_comment_create(data: Dict) -> Dict:
        """이슈 댓글 생성 데이터 역직렬화"""
        return Serializer.deserialize(data, issue_comment_create_schema)

    @staticmethod
    def deserialize_issue_resolve(data: Dict) -> Dict:
        """이슈 해결 데이터 역직렬화"""
        return Serializer.deserialize(data, issue_resolve_schema)
