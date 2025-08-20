from flask import Blueprint, request
import logging
from app.models.db import get_db_session
from app.utils.notifications import SlackNotifier
from app.serializers import (
    NoticeSerializer,
    json_response,
    error_json_response,
    handle_serialization_errors,
)
from app.services import NoticeService

notices_bp = Blueprint("notices", __name__)
logger = logging.getLogger(__name__)


# SlackNotifier 인스턴스를 전역 변수로 생성하지 않음
@notices_bp.route("/notices", methods=["POST"])
@handle_serialization_errors
def add_notice():
    """
    공지사항 추가 API
    ---
    tags:
      - Notices
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - title
            - content
            - created_by
          properties:
            title:
              type: string
              description: 공지사항 제목
            content:
              type: string
              description: 공지사항 내용
            created_by:
              type: string
              description: 작성자명
            type:
              type: string
              description: 공지사항 유형, 기본값은 공지사항
    responses:
      201:
        description: 공지사항 추가 성공
      400:
        description: 필수 데이터 누락
      403:
        description: 권한 없음
      500:
        description: 서버 오류
    """
    try:
        data = request.json
        if not data:
            return error_json_response("요청 데이터가 없습니다.", status_code=400)

        # DB 작업 - Serializer 사용
        session = get_db_session()
        try:
            # 데이터 검증
            validated_data = NoticeSerializer.deserialize_notice_create(data)
            # Service를 사용한 공지사항 추가
            notice = NoticeService.create_notice(session, validated_data)
            notice_data = NoticeSerializer.serialize_notice(notice)
            session.commit()

        except Exception as e:
            session.rollback()
            logger.error(f"공지사항 추가 중 오류: {str(e)}")
            return error_json_response(
                "공지사항 추가 중 오류가 발생했습니다.", status_code=500
            )
        finally:
            session.close()

        # Slack 알림 전송 (channel -> channel_type으로 수정)
        notifier = SlackNotifier()
        notification_message = f"새로운 공지사항이 등록되었습니다!\n제목: {notice_data['title']}\n작성자: {notice_data['created_by']}"
        notifier.send_notification(notification_message, channel_type="notice")

        return json_response(notice_data, status_code=201)
    except Exception as e:
        logger.error(f"공지사항 추가 중 오류: {str(e)}")
        return error_json_response("공지사항 추가 실패", status_code=500)


@notices_bp.route("/notices", methods=["GET"])
def get_notices():
    """
    공지사항 조회 API
    ---
    tags:
      - Notices
    responses:
      200:
        description: 모든 공지사항 데이터를 포함한 응답
      500:
        description: 공지사항을 불러오는 데 실패함
    """
    try:
        session = get_db_session()

        # Service를 사용한 공지사항 조회
        notices = NoticeService.get_notices(session)

        session.close()
        return json_response({"data": notices}), 200
    except Exception as e:
        logger.error("Error retrieving notices", exc_info=True)
        return (
            error_json_response("공지사항을 불러오는데 실패했습니다.", status_code=500),
            500,
        )


@notices_bp.route("/notices/<int:notice_id>", methods=["PUT"])
@handle_serialization_errors
def update_notice(notice_id):
    """
    공지사항 수정 API
    ---
    tags:
      - Notices
    parameters:
      - name: notice_id
        in: path
        type: integer
        required: true
        description: 수정할 공지사항 ID
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
              example: "수정된 공지사항 제목"
            content:
              type: string
              example: "수정된 공지사항 내용입니다."
            type:
              type: string
              example: "공지사항"
            username:
              type: string
              example: "홍길동"
    responses:
      200:
        description: 공지사항 수정 성공
      400:
        description: 필수 데이터 누락
      404:
        description: 공지사항을 찾을 수 없음
      500:
        description: 서버 오류 발생
    """
    try:
        data = request.json
        if not data:
            return error_json_response("요청 데이터가 없습니다.", status_code=400)

        session = get_db_session()
        try:
            # 데이터 검증
            validated_data = NoticeSerializer.deserialize_notice_update(data)
            # Service를 사용한 공지사항 수정
            notice = NoticeService.update_notice(session, notice_id, validated_data)
            serialized_notice = NoticeSerializer.serialize_notice(notice)
            session.commit()

        except Exception as e:
            session.rollback()
            logger.error(f"공지사항 수정 중 오류: {str(e)}")
            return error_json_response(
                "공지사항 수정 중 오류가 발생했습니다.", status_code=500
            )
        finally:
            session.close()

        return json_response(serialized_notice), 200

    except Exception as e:
        logger.error("공지사항 수정 오류", exc_info=True)
        return (
            error_json_response(
                "공지사항 수정 중 오류가 발생했습니다.", status_code=500
            ),
            500,
        )


@notices_bp.route("/notices/<int:notice_id>", methods=["DELETE"])
@handle_serialization_errors
def delete_notice(notice_id):
    """
    공지사항 삭제 API
    ---
    tags:
      - Notices
    parameters:
      - name: notice_id
        in: path
        type: integer
        required: true
        description: 삭제할 공지사항 ID
    responses:
      200:
        description: 공지사항 삭제 성공
      404:
        description: 공지사항을 찾을 수 없음
      500:
        description: 서버 오류 발생
    """
    try:
        session = get_db_session()
        try:
            # Service를 사용한 공지사항 삭제
            notice = NoticeService.delete_notice(session, notice_id)
            serialized_notice = NoticeSerializer.serialize_notice(notice)
            session.commit()

        except Exception as e:
            session.rollback()
            logger.error(f"공지사항 삭제 중 오류: {str(e)}")
            return error_json_response(
                "공지사항 삭제 중 오류가 발생했습니다.", status_code=500
            )
        finally:
            session.close()

        return json_response(serialized_notice), 200

    except Exception as e:
        logger.error("공지사항 삭제 오류", exc_info=True)
        return (
            error_json_response(
                "공지사항 삭제 중 오류가 발생했습니다.", status_code=500
            ),
            500,
        )


@notices_bp.route("/notices/read", methods=["POST"])
@handle_serialization_errors
def mark_notice_read():
    """
    공지사항 읽음 표시 API
    ---
    tags:
      - Notices
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - notice_id
            - username
          properties:
            notice_id:
              type: integer
              example: 1
            username:
              type: string
              example: "홍길동"
    responses:
      201:
        description: 읽음 표시 성공
      400:
        description: 필수 데이터 누락
      500:
        description: 서버 오류 발생
    """
    try:
        data = request.json
        if not data:
            return error_json_response("요청 데이터가 없습니다.", status_code=400)

        session = get_db_session()
        try:
            # 데이터 검증
            validated_data = NoticeSerializer.deserialize_notice_read_create(data)
            # Service를 사용한 공지사항 읽음 표시
            notice_read = NoticeService.mark_notice_read(session, validated_data)
            serialized_notice_read = NoticeSerializer.serialize_notice_read(notice_read)
            session.commit()

        except Exception as e:
            session.rollback()
            logger.error(f"공지사항 읽음 표시 중 오류: {str(e)}")
            return error_json_response("공지사항 읽음 표시 실패", status_code=500)
        finally:
            session.close()

        return json_response(serialized_notice_read), 201
    except Exception as e:
        logger.error("공지사항 읽음 표시 오류", exc_info=True)
        return error_json_response("공지사항 읽음 표시 실패", status_code=500)


@notices_bp.route("/notices/reads", methods=["GET"])
@handle_serialization_errors
def get_notice_reads():
    """
    공지사항별 읽은 사용자 목록 조회 API
    ---
    tags:
      - Notices
    parameters:
      - name: notice_id
        in: query
        type: integer
        required: true
        description: "조회할 공지사항 ID"
    responses:
      200:
        description: 공지사항을 읽은 사용자 목록 반환
      400:
        description: 공지사항 ID 누락
      500:
        description: 서버 오류 발생
    """
    try:
        notice_id = request.args.get("notice_id")

        session = get_db_session()
        try:
            # Service를 사용한 공지사항 읽음 목록 조회
            reads_data = NoticeService.get_notice_reads(session, int(notice_id))

            session.close()
            return json_response({"data": reads_data}), 200

        except Exception as e:
            session.close()
            logger.error(f"공지사항 읽음 목록 조회 중 오류: {str(e)}")
            return (
                error_json_response("공지사항 읽음 목록 조회 실패", status_code=500),
                500,
            )
    except Exception as e:
        logger.error("공지사항 읽음 목록 조회 오류", exc_info=True)
        return (
            error_json_response("공지사항 읽음 목록 조회 실패", status_code=500),
            500,
        )
