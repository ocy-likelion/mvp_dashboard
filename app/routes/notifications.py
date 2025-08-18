from flask import Blueprint, request
from app.models.db import get_db_session
from app.utils.notifications import SlackNotifier
import logging

from app.serializers import (
    NotificationSerializer,
    handle_serialization_errors,
    json_response,
    error_json_response,
)

notifications_bp = Blueprint("notifications", __name__)
logger = logging.getLogger(__name__)
slack_notifier = SlackNotifier()


@notifications_bp.route("/notifications/unread-count", methods=["GET"])
@handle_serialization_errors
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
        # 쿼리 파라미터를 딕셔너리로 변환
        query_data = {"username": request.args.get("username")}

        session = get_db_session()
        try:
            # Serializer를 사용한 미확인 알림 개수 조회 (검증 포함)
            unread_counts = NotificationSerializer.get_unread_count(session, query_data)
            session.commit()

            return json_response(
                data=unread_counts,
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
