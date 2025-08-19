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
)
from app.models.models import Issue, IssueComment


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

    @staticmethod
    def create_issue(session, data: Dict) -> Dict:
        """이슈 생성"""
        # 데이터 검증
        validated_data = IssueSerializer.deserialize_issue_create(data)

        # 이슈 생성
        issue = Issue(
            content=validated_data["content"],
            training_course=validated_data.get("training_course"),
            username=validated_data.get("username"),
            created_by=validated_data.get("created_by", validated_data.get("username")),
            date=validated_data.get("date"),
            resolved=False,
        )

        session.add(issue)
        session.flush()  # ID를 얻기 위해 flush

        return {"id": issue.id, **validated_data}

    @staticmethod
    def get_issues(session) -> List[Dict]:
        """해결되지 않은 이슈 목록 조회"""
        # ORM을 사용하여 해결되지 않은 이슈 조회
        issues_query = (
            session.query(Issue)
            .filter(Issue.resolved == False)
            .order_by(Issue.created_at.desc())
        )
        issues = issues_query.all()

        # Serializer를 사용한 데이터 직렬화
        serialized_issues = IssueSerializer.serialize_issues(issues)

        # 교육과정별로 그룹화
        issues_grouped = {}
        for issue, serialized_issue in zip(issues, serialized_issues):
            course = issue.training_course
            if course not in issues_grouped:
                issues_grouped[course] = []

            # 댓글 조회 및 직렬화
            comments = (
                session.query(IssueComment)
                .filter(IssueComment.issue_id == issue.id)
                .all()
            )
            serialized_comments = IssueSerializer.serialize_issue_comments(comments)

            # 댓글 정보를 이슈에 추가
            serialized_issue["comments"] = serialized_comments
            issues_grouped[course].append(serialized_issue)

        # 응답 형식 변환
        response_data = [
            {"training_course": course, "issues": issues_list}
            for course, issues_list in issues_grouped.items()
        ]

        return response_data

    @staticmethod
    def add_comment(session, data: Dict):
        """이슈 댓글 추가"""
        # 데이터 검증
        validated_data = IssueSerializer.deserialize_issue_comment_create(data)

        # 댓글 생성
        comment = IssueComment(
            issue_id=validated_data["issue_id"],
            comment=validated_data["comment"],
            created_by=validated_data["created_by"],
        )

        session.add(comment)
        session.flush()  # ID를 얻기 위해 flush

        return {"id": comment.id, **validated_data}

    @staticmethod
    def resolve_issue(session, data: Dict):
        """이슈 해결"""
        # 데이터 검증
        validated_data = IssueSerializer.deserialize_issue_resolve(data)

        issue = (
            session.query(Issue).filter(Issue.id == validated_data["issue_id"]).first()
        )
        if not issue:
            raise ValueError("이슈를 찾을 수 없습니다.")

        issue.resolved = True

        # 업데이트된 이슈 직렬화
        return IssueSerializer.serialize_issue(issue)

    @staticmethod
    def get_issue_comments(session, issue_id: str) -> List[Dict]:
        """특정 이슈에 대한 댓글 목록 조회"""
        if not issue_id:
            raise ValueError("이슈 ID를 입력하세요.")

        comments_query = (
            session.query(IssueComment)
            .filter(IssueComment.issue_id == issue_id)
            .order_by(IssueComment.created_at.asc())
        )

        comments = comments_query.all()

        # Serializer를 사용한 데이터 직렬화
        return IssueSerializer.serialize_issue_comments(comments)

    @staticmethod
    def get_all_issues(session) -> List[Dict]:
        """모든 이슈 목록 조회 (다운로드용)"""
        issues_query = session.query(Issue).all()

        # Serializer를 사용한 데이터 직렬화
        return IssueSerializer.serialize_issues(issues_query)
