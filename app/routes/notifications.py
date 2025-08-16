# app/routes/notifications.py
from flask import Blueprint, request, jsonify
from datetime import datetime
from app.models.db import get_db_session
from app.models.models import UserLastCheck, Notice, Issue, IssueComment
from app.utils.notifications import SlackNotifier
import logging

from app.serializers import (
    json_response,
    error_json_response,
)

notifications_bp = Blueprint("notifications", __name__)
logger = logging.getLogger(__name__)
slack_notifier = SlackNotifier()


@notifications_bp.route("/notifications/unread-count", methods=["GET"])
def get_unread_count():
    """
    사용자별 미확인 알림 개수 조회 API
    ---
    tags:
      - Notifications
    parameters:
      - name: username
        in: query
        type: string
        required: true
        description: 사용자명
    responses:
      200:
        description: 미확인 알림 개수 반환
      400:
        description: 사용자명 누락
      500:
        description: 서버 오류
    """
    try:
        username = request.args.get("username")
        if not username:
            return error_json_response("사용자명이 필요합니다.", status_code=400)

        session = get_db_session()
        try:
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
                session.commit()
                return json_response(
                    data={
                        "new_notices": 0,
                        "new_issues": 0,
                        "new_comments": 0,
                    },
                    message="미확인 알림 개수 조회 성공",
                    status_code=200,
                )

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
            session.commit()

            return json_response(
                data={
                    "new_notices": new_notices,
                    "new_issues": new_issues,
                    "new_comments": new_comments,
                },
                message="미확인 알림 개수 조회 성공",
                status_code=200,
            )

        except Exception as e:
            session.rollback()
            logger.error(f"알림 개수 조회 중 오류: {str(e)}")
            return error_json_response("알림 개수 조회 실패", status_code=500)
        finally:
            session.close()

    except Exception as e:
        logger.error("알림 개수 조회 오류", exc_info=True)
        return error_json_response("알림 개수 조회 실패", status_code=500)



