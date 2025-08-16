from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
from app.models.db import get_db_session
from app.models.models import Notice, NoticeRead, User
from app.utils.notifications import SlackNotifier
import os
from app.serializers import (
    NoticeSerializer,
    json_response,
    error_json_response,
    handle_serialization_errors,
)

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

        # 스키마를 사용한 데이터 검증
        validated_data = NoticeSerializer.deserialize_notice_create(data)

        # 허용된 사용자 확인
        allowed_users = ["김은지", "장지연", "김슬기"]
        if validated_data.get("created_by") not in allowed_users:
            return error_json_response(
                "공지사항 작성 권한이 없습니다.", status_code=403
            )

        # DB 작업 - ORM 사용
        session = get_db_session()
        try:
            # 공지사항 생성
            notice = Notice(
                title=validated_data["title"],
                content=validated_data["content"],
                type=validated_data.get("type", "공지사항"),
                created_by=validated_data.get("created_by"),
            )

            session.add(notice)
            session.commit()

            notice_id = notice.id

            # 저장된 공지사항 직렬화
            serialized_notice = NoticeSerializer.serialize_notice(notice)

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
        notification_message = f"새로운 공지사항이 등록되었습니다!\n제목: {validated_data['title']}\n작성자: {validated_data['created_by']}"
        notifier.send_notification(notification_message, channel_type="notice")

        return json_response(serialized_notice, status_code=201)
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

        # ORM을 사용하여 공지사항 조회
        notices_query = (
            session.query(Notice)
            .filter(Notice.is_deleted == False)
            .order_by(Notice.date.desc())
        )
        notices = []

        for notice in notices_query.all():
            notice_dict = {
                "id": notice.id,
                "type": notice.type or "공지사항",
                "title": notice.title,
                "content": notice.content,
                "date": notice.date.strftime("%Y-%m-%d %H:%M:%S"),
                "created_by": notice.created_by,
            }
            notices.append(notice_dict)

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

        # 스키마를 사용한 데이터 검증
        validated_data = NoticeSerializer.deserialize_notice_update(data)

        # 수정자 정보 추출
        username = validated_data.get("username")

        if not username:
            return error_json_response("수정자 정보가 누락되었습니다.", status_code=400)

        session = get_db_session()
        try:
            # 공지사항 존재 확인
            notice = session.query(Notice).filter(Notice.id == notice_id).first()

            if not notice:
                return error_json_response(
                    "해당 공지사항을 찾을 수 없습니다.", status_code=404
                )

            # 공지사항 업데이트
            notice.title = validated_data.get("title")
            notice.content = validated_data.get("content")
            notice.type = validated_data.get("type")
            notice.modified_by = username

            session.commit()

            # 수정된 공지사항 직렬화
            serialized_notice = NoticeSerializer.serialize_notice(notice)

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
            # 공지사항 존재 확인
            notice = session.query(Notice).filter(Notice.id == notice_id).first()

            if not notice:
                return error_json_response(
                    "해당 공지사항을 찾을 수 없습니다.", status_code=404
                )

            # 공지사항 삭제 (soft delete)
            notice.is_deleted = True
            session.commit()

            # 삭제된 공지사항 직렬화
            serialized_notice = NoticeSerializer.serialize_notice(notice)

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

        # 스키마를 사용한 데이터 검증
        validated_data = NoticeSerializer.deserialize_notice_read(data)

        notice_id = validated_data.get("notice_id")
        username = validated_data.get("username")

        if not notice_id or not username:
            return error_json_response(
                "공지사항 ID와 사용자 이름이 필요합니다.", status_code=400
            )

        session = get_db_session()
        try:
            # 공지사항 존재 확인
            notice = session.query(Notice).filter(Notice.id == notice_id).first()
            if not notice:
                return error_json_response(
                    "공지사항을 찾을 수 없습니다.", status_code=404
                )

            # 이미 읽었는지 확인
            existing_read = (
                session.query(NoticeRead)
                .filter(
                    NoticeRead.notice_id == notice_id, NoticeRead.username == username
                )
                .first()
            )

            if not existing_read:
                # 읽음 표시 추가
                notice_read = NoticeRead(notice_id=notice_id, username=username)
                session.add(notice_read)
                session.commit()

            # 읽음 표시 직렬화
            serialized_notice_read = NoticeSerializer.serialize_notice_read(notice_read)

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

        if not notice_id:
            return error_json_response("공지사항 ID가 필요합니다.", status_code=400)

        session = get_db_session()
        try:
            # 공지사항 읽음 기록 조회
            reads_query = (
                session.query(NoticeRead)
                .filter(NoticeRead.notice_id == notice_id)
                .order_by(NoticeRead.read_at.desc())
            )

            reads_data = []
            for notice_read in reads_query.all():
                reads_data.append(
                    {
                        "username": notice_read.username,
                        "read_at": notice_read.read_at.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )

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
