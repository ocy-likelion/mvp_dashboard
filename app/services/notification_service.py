"""
Notification service for notification-related business logic
"""

from typing import Dict
from datetime import datetime
from sqlalchemy.orm import Session

from .base_service import BaseService
from app.models.models import UserLastCheck, Notice, Issue, IssueComment


class NotificationService(BaseService):
    """알림 관련 비즈니스 로직 처리"""

    @staticmethod
    def get_unread_count(session: Session, validated_data: Dict) -> Dict:
        """사용자별 미확인 알림 개수 조회"""
        BaseService.validate_db_session(session)

        username = validated_data["username"]

        # 사용자의 마지막 확인 시간 조회
        last_check = (
            session.query(UserLastCheck)
            .filter(UserLastCheck.username == username)
            .first()
        )

        if not last_check:
            # 첫 로그인인 경우 현재 시간으로 초기화
            last_check = UserLastCheck(
                username=username,
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

        return {
            "new_notices": new_notices,
            "new_issues": new_issues,
            "new_comments": new_comments,
        }

    @staticmethod
    def update_last_check_time(session: Session, validated_data: Dict) -> UserLastCheck:
        """사용자의 마지막 확인 시간 업데이트"""
        BaseService.validate_db_session(session)

        username = validated_data["username"]
        check_type = validated_data.get("check_type", "all")

        valid_check_types = ["all", "notice", "issue", "comment"]
        if check_type not in valid_check_types:
            raise ValueError(f"유효하지 않은 확인 타입입니다: {check_type}")

        # 사용자의 마지막 확인 시간 조회 또는 생성
        last_check = (
            session.query(UserLastCheck)
            .filter(UserLastCheck.username == username)
            .first()
        )

        current_time = datetime.now()

        if not last_check:
            last_check = UserLastCheck(
                username=username,
                last_notice_check=current_time,
                last_issue_check=current_time,
                last_comment_check=current_time,
            )
            session.add(last_check)
        else:
            # 특정 타입만 업데이트
            if check_type == "all":
                last_check.last_notice_check = current_time
                last_check.last_issue_check = current_time
                last_check.last_comment_check = current_time
            elif check_type == "notice":
                last_check.last_notice_check = current_time
            elif check_type == "issue":
                last_check.last_issue_check = current_time
            elif check_type == "comment":
                last_check.last_comment_check = current_time

        session.flush()
        return last_check
