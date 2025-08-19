from typing import Dict
from datetime import datetime

from .base import Serializer
from app.schemas import notification_query_schema
from app.models.models import UserLastCheck, Notice, Issue, IssueComment


class NotificationSerializer:
    """알림 관련 직렬화 함수들"""

    @staticmethod
    def deserialize_notification_query(data: Dict) -> Dict:
        """알림 조회 데이터 역직렬화"""
        return Serializer.deserialize(data, notification_query_schema)

    @staticmethod
    def get_unread_count(session, data: Dict) -> Dict:
        """사용자별 미확인 알림 개수 조회"""
        # 데이터 검증
        validated_data = NotificationSerializer.deserialize_notification_query(data)

        # 사용자의 마지막 확인 시간 조회
        last_check = (
            session.query(UserLastCheck)
            .filter(UserLastCheck.username == validated_data["username"])
            .first()
        )

        if not last_check:
            # 첫 로그인인 경우 현재 시간으로 초기화
            last_check = UserLastCheck(
                username=validated_data["username"],
                last_notice_check=datetime.now(),
                last_issue_check=datetime.now(),
                last_comment_check=datetime.now(),
            )
            session.add(last_check)
            session.flush()  # 커밋하지 않고 flush만 실행
            return {
                "new_notices": 0,
                "new_issues": 0,
                "new_comments": 0,
            }

        # 새로운 항목 개수 조회
        new_notices = (
            session.query(Notice)
            .filter(
                Notice.date > last_check.last_notice_check,
                Notice.is_deleted == False,
            )
            .count()
        )

        new_issues = (
            session.query(Issue)
            .filter(Issue.created_at > last_check.last_issue_check)
            .count()
        )

        new_comments = (
            session.query(IssueComment)
            .filter(IssueComment.created_at > last_check.last_comment_check)
            .count()
        )

        # 현재 시간으로 마지막 확인 시간 업데이트
        last_check.last_notice_check = datetime.now()
        last_check.last_issue_check = datetime.now()
        last_check.last_comment_check = datetime.now()

        return {
            "new_notices": new_notices,
            "new_issues": new_issues,
            "new_comments": new_comments,
        }
