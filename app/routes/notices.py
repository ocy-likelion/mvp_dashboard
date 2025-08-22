from flask import Blueprint, request
import logging
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
    summary: 새로운 공지사항 생성
    description: |
      새로운 공지사항을 생성합니다. 생성 후 Slack 알림이 자동으로 전송됩니다.
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/notices', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          title: '중요 공지사항',
          content: '내일 오후 2시에 전체 회의가 있습니다.',
          created_by: '관리자',
          type: '공지사항'
        })
      });
      
      const result = await response.json();
      console.log(result);
      ```
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
              example: "중요 공지사항"
            content:
              type: string
              description: 공지사항 내용
              example: "내일 오후 2시에 전체 회의가 있습니다."
            created_by:
              type: string
              description: 작성자명
              example: "관리자"
            type:
              type: string
              description: 공지사항 유형, 기본값은 공지사항
              example: "공지사항"
    responses:
      201:
        description: 공지사항 추가 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            error:
              type: string
              example: "공지사항이 성공적으로 생성되었습니다."
            data:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                title:
                  type: string
                  example: "중요 공지사항"
                content:
                  type: string
                  example: "내일 오후 2시에 전체 회의가 있습니다."
                created_by:
                  type: string
                  example: "관리자"
                type:
                  type: string
                  example: "공지사항"
                created_at:
                  type: string
                  format: date-time
                  example: "2025-01-15T10:30:00"
            status_code:
              type: integer
              example: 201
        examples:
          application/json:
            summary: 공지사항 생성 성공 응답
            value:
              success: true
              error: "공지사항이 성공적으로 생성되었습니다."
              data:
                id: 1
                title: "중요 공지사항"
                content: "내일 오후 2시에 전체 회의가 있습니다."
                created_by: "관리자"
                type: "공지사항"
                created_at: "2025-01-15T10:30:00"
              status_code: 201
      400:
        description: 필수 데이터 누락
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "제목, 내용, 작성자는 필수 입력 항목입니다."
            status_code:
              type: integer
              example: 400
      403:
        description: 권한 없음
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "공지사항 작성 권한이 없습니다."
            status_code:
              type: integer
              example: 403
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
              example: "공지사항 추가 실패"
            status_code:
              type: integer
              example: 500
    """
    try:
        validated_data = NoticeSerializer.deserialize_notice_create(request.json)
        notice_data = NoticeService.create_notice(validated_data)
        
        # Slack 알림 전송 (channel -> channel_type으로 수정)
        notifier = SlackNotifier()
        notification_message = f"새로운 공지사항이 등록되었습니다!\n제목: {notice_data['title']}\n작성자: {notice_data['created_by']}"
        notifier.send_notification(notification_message, channel_type="notice")

        return json_response(notice_data, message="공지사항이 성공적으로 생성되었습니다.", status_code=201)
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
    summary: 모든 공지사항 목록 조회
    description: |
      등록된 모든 공지사항을 조회합니다.
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/notices', {
        method: 'GET',
        credentials: 'include'
      });
      
      const result = await response.json();
      console.log(result);
      ```
    responses:
      200:
        description: 모든 공지사항 데이터를 포함한 응답
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            error:
              type: string
              example: "공지사항 조회 성공"
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  title:
                    type: string
                    example: "중요 공지사항"
                  content:
                    type: string
                    example: "내일 오후 2시에 전체 회의가 있습니다."
                  created_by:
                    type: string
                    example: "관리자"
                  type:
                    type: string
                    example: "공지사항"
                  created_at:
                    type: string
                    format: date-time
                    example: "2025-01-15T10:30:00"
            status_code:
              type: integer
              example: 200
        examples:
          application/json:
            summary: 공지사항 목록 조회 성공 응답
            value:
              success: true
              error: "공지사항 조회 성공"
              data:
                - id: 1
                  title: "중요 공지사항"
                  content: "내일 오후 2시에 전체 회의가 있습니다."
                  created_by: "관리자"
                  type: "공지사항"
                  created_at: "2025-01-15T10:30:00"
                - id: 2
                  title: "시스템 점검 안내"
                  content: "오늘 밤 12시부터 2시간 동안 시스템 점검이 있습니다."
                  created_by: "시스템관리자"
                  type: "안내"
                  created_at: "2025-01-14T15:20:00"
              status_code: 200
      500:
        description: 공지사항을 불러오는 데 실패함
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "공지사항을 불러오는데 실패했습니다."
            status_code:
              type: integer
              example: 500
    """
    try:
        notices_data = NoticeService.get_notices()
        # 서비스에서 이미 딕셔너리 형태로 반환되므로 직렬화 불필요
        return json_response(
            data=notices_data, message="공지사항 조회 성공", status_code=200
        )
    except Exception as e:
        logger.error("Error retrieving notices", exc_info=True)
        return error_json_response("공지사항을 불러오는데 실패했습니다.", status_code=500)


@notices_bp.route("/notices/<int:notice_id>", methods=["PUT"])
@handle_serialization_errors
def update_notice(notice_id):
    """
    공지사항 수정 API
    ---
    tags:
      - Notices
    summary: 기존 공지사항 수정
    description: |
      지정된 ID의 공지사항을 수정합니다.
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/notices/1', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          title: '수정된 공지사항 제목',
          content: '수정된 공지사항 내용입니다.',
          type: '공지사항',
          username: '홍길동'
        })
      });
      
      const result = await response.json();
      console.log(result);
      ```
    parameters:
      - name: notice_id
        in: path
        type: integer
        required: true
        description: 수정할 공지사항 ID
        example: 1
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
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            error:
              type: string
              example: "공지사항이 성공적으로 수정되었습니다."
            data:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                title:
                  type: string
                  example: "수정된 공지사항 제목"
                content:
                  type: string
                  example: "수정된 공지사항 내용입니다."
                created_by:
                  type: string
                  example: "관리자"
                type:
                  type: string
                  example: "공지사항"
                created_at:
                  type: string
                  format: date-time
                  example: "2025-01-15T10:30:00"
            status_code:
              type: integer
              example: 200
        examples:
          application/json:
            summary: 공지사항 수정 성공 응답
            value:
              success: true
              error: "공지사항이 성공적으로 수정되었습니다."
              data:
                id: 1
                title: "수정된 공지사항 제목"
                content: "수정된 공지사항 내용입니다."
                created_by: "관리자"
                type: "공지사항"
                created_at: "2025-01-15T10:30:00"
              status_code: 200
      400:
        description: 필수 데이터 누락
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "수정할 내용을 입력해주세요."
            status_code:
              type: integer
              example: 400
      404:
        description: 공지사항을 찾을 수 없음
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "해당 공지사항을 찾을 수 없습니다."
            status_code:
              type: integer
              example: 404
      500:
        description: 서버 오류 발생
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "공지사항 수정 중 오류가 발생했습니다."
            status_code:
              type: integer
              example: 500
    """
    try:
        validated_data = NoticeSerializer.deserialize_notice_update(request.json)
        notice = NoticeService.update_notice(notice_id, validated_data)
        serialized_notice = NoticeSerializer.serialize_notice(notice)
        return json_response(serialized_notice, message="공지사항이 성공적으로 수정되었습니다.", status_code=200)

    except Exception as e:
        logger.error("공지사항 수정 오류", exc_info=True)
        return error_json_response(
            "공지사항 수정 중 오류가 발생했습니다.", status_code=500
        )


@notices_bp.route("/notices/<int:notice_id>", methods=["DELETE"])
@handle_serialization_errors
def delete_notice(notice_id):
    """
    공지사항 삭제 API
    ---
    tags:
      - Notices
    summary: 공지사항 삭제
    description: |
      지정된 ID의 공지사항을 삭제합니다.
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/notices/1', {
        method: 'DELETE',
        credentials: 'include'
      });
      
      const result = await response.json();
      console.log(result);
      ```
    parameters:
      - name: notice_id
        in: path
        type: integer
        required: true
        description: 삭제할 공지사항 ID
        example: 1
    responses:
      200:
        description: 공지사항 삭제 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            error:
              type: string
              example: "공지사항이 성공적으로 삭제되었습니다."
            data:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                title:
                  type: string
                  example: "삭제된 공지사항"
                content:
                  type: string
                  example: "삭제된 공지사항 내용"
                created_by:
                  type: string
                  example: "관리자"
                type:
                  type: string
                  example: "공지사항"
                created_at:
                  type: string
                  format: date-time
                  example: "2025-01-15T10:30:00"
            status_code:
              type: integer
              example: 200
        examples:
          application/json:
            summary: 공지사항 삭제 성공 응답
            value:
              success: true
              error: "공지사항이 성공적으로 삭제되었습니다."
              data:
                id: 1
                title: "삭제된 공지사항"
                content: "삭제된 공지사항 내용"
                created_by: "관리자"
                type: "공지사항"
                created_at: "2025-01-15T10:30:00"
              status_code: 200
      404:
        description: 공지사항을 찾을 수 없음
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "해당 공지사항을 찾을 수 없습니다."
            status_code:
              type: integer
              example: 404
      500:
        description: 서버 오류 발생
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "공지사항 삭제 중 오류가 발생했습니다."
            status_code:
              type: integer
              example: 500
    """
    try:
        notice = NoticeService.delete_notice(notice_id)
        serialized_notice = NoticeSerializer.serialize_notice(notice)

        return json_response(serialized_notice, message="공지사항이 성공적으로 삭제되었습니다.", status_code=200)

    except Exception as e:
        logger.error("공지사항 삭제 오류", exc_info=True)
        return error_json_response(
            "공지사항 삭제 중 오류가 발생했습니다.", status_code=500
        )


@notices_bp.route("/notices/read", methods=["POST"])
@handle_serialization_errors
def mark_notice_read():
    """
    공지사항 읽음 표시 API
    ---
    tags:
      - Notices
    summary: 공지사항 읽음 표시
    description: |
      특정 사용자가 공지사항을 읽었다고 표시합니다.
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/notices/read', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          notice_id: 1,
          username: '홍길동'
        })
      });
      
      const result = await response.json();
      console.log(result);
      ```
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
              description: 공지사항 ID
              example: 1
            username:
              type: string
              description: 사용자명
              example: "홍길동"
    responses:
      201:
        description: 읽음 표시 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            error:
              type: string
              example: "읽음 표시가 완료되었습니다."
            data:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                notice_id:
                  type: integer
                  example: 1
                username:
                  type: string
                  example: "홍길동"
                read_at:
                  type: string
                  format: date-time
                  example: "2025-01-15T11:00:00"
            status_code:
              type: integer
              example: 201
        examples:
          application/json:
            summary: 읽음 표시 성공 응답
            value:
              success: true
              error: "읽음 표시가 완료되었습니다."
              data:
                id: 1
                notice_id: 1
                username: "홍길동"
                read_at: "2025-01-15T11:00:00"
              status_code: 201
      400:
        description: 필수 데이터 누락
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "공지사항 ID와 사용자명을 입력해주세요."
            status_code:
              type: integer
              example: 400
      500:
        description: 서버 오류 발생
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "공지사항 읽음 표시 실패"
            status_code:
              type: integer
              example: 500
    """
    try:
        validated_data = NoticeSerializer.deserialize_notice_read_create(request.json)
        notice_read = NoticeService.mark_notice_read(validated_data)
        serialized_notice_read = NoticeSerializer.serialize_notice_read(notice_read)
        return json_response(serialized_notice_read, message="읽음 표시가 완료되었습니다.", status_code=201)
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
    summary: 공지사항을 읽은 사용자 목록 조회
    description: |
      특정 공지사항을 읽은 사용자들의 목록을 조회합니다.
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/notices/reads?notice_id=1', {
        method: 'GET',
        credentials: 'include'
      });
      
      const result = await response.json();
      console.log(result);
      ```
    parameters:
      - name: notice_id
        in: query
        type: integer
        required: true
        description: "조회할 공지사항 ID"
        example: 1
    responses:
      200:
        description: 공지사항을 읽은 사용자 목록 반환
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            error:
              type: string
              example: "공지사항 읽음 목록 조회 성공"
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  username:
                    type: string
                    example: "홍길동"
                  read_at:
                    type: string
                    format: date-time
                    example: "2025-01-15T11:00:00"
            status_code:
              type: integer
              example: 200
        examples:
          application/json:
            summary: 읽은 사용자 목록 조회 성공 응답
            value:
              success: true
              error: "공지사항 읽음 목록 조회 성공"
              data:
                - id: 1
                  username: "홍길동"
                  read_at: "2025-01-15T11:00:00"
                - id: 2
                  username: "김철수"
                  read_at: "2025-01-15T11:30:00"
              status_code: 200
      400:
        description: 공지사항 ID 누락
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "공지사항 ID를 입력해주세요."
            status_code:
              type: integer
              example: 400
      500:
        description: 서버 오류 발생
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "공지사항 읽음 목록 조회 실패"
            status_code:
              type: integer
              example: 500
    """
    try:
        validated_data = NoticeSerializer.deserialize_notice_read_get(request.args)
        reads_data = NoticeService.get_notice_reads(validated_data)
        serialized_reads_data = NoticeSerializer.serialize_notice_reads(reads_data)

        return json_response(
            data=serialized_reads_data,
            message="공지사항 읽음 목록 조회 성공",
            status_code=200,
        )
    except Exception as e:
        logger.error("공지사항 읽음 목록 조회 오류", exc_info=True)
        return (
            error_json_response("공지사항 읽음 목록 조회 실패", status_code=500),
            500,
        )
