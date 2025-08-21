from flask import Blueprint, request
from app.utils.notifications import SlackNotifier
import logging

from app.serializers import (
    NotificationSerializer,
    handle_serialization_errors,
    json_response,
    error_json_response,
)
from app.services import NotificationService

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

        # 데이터 검증
        validated_data = NotificationSerializer.deserialize_notification_query(
            query_data
        )
        # Service를 사용한 미확인 알림 개수 조회 및 마지막 확인 시간 업데이트
        validated_data["check_type"] = "all"
        unread_counts = NotificationService.get_unread_count(validated_data)
        NotificationService.update_last_check_time(validated_data)

        return json_response(
            data=unread_counts,
            message="미확인 알림 개수 조회 성공",
            status_code=200,
        )

    except Exception as e:
        logger.error("알림 개수 조회 오류", exc_info=True)
        return error_json_response("알림 개수 조회 실패", status_code=500)
