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
    summary: 사용자별 미확인 알림 개수 조회
    description: |
      특정 사용자의 미확인 알림 개수를 조회하고 마지막 확인 시간을 업데이트합니다.
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/notifications/unread-count?username=홍길동', {
        method: 'GET',
        credentials: 'include'
      });
      
      const result = await response.json();
      console.log(result);
      ```
    parameters:
      - name: username
        in: query
        type: string
        required: true
        description: 사용자명
        example: "홍길동"
    responses:
      200:
        description: 미확인 알림 개수 반환
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            error:
              type: string
              example: "미확인 알림 개수 조회 성공"
            data:
              type: object
              properties:
                username:
                  type: string
                  example: "홍길동"
                unread_count:
                  type: integer
                  example: 5
                last_check_time:
                  type: string
                  format: date-time
                  example: "2025-01-15T10:30:00"
            status_code:
              type: integer
              example: 200
        examples:
          application/json:
            summary: 미확인 알림 개수 조회 성공 응답
            value:
              success: true
              error: "미확인 알림 개수 조회 성공"
              data:
                username: "홍길동"
                unread_count: 5
                last_check_time: "2025-01-15T10:30:00"
              status_code: 200
      400:
        description: 사용자명 누락
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "사용자명을 입력해주세요."
            status_code:
              type: integer
              example: 400
      500:
        description: 서버 오류
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "알림 개수 조회 실패"
            status_code:
              type: integer
              example: 500
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
