from flask import Blueprint, request, send_file
import io
import pandas as pd
import logging

from app.utils.notifications import SlackNotifier
from app.serializers import (
    IssueSerializer,
    json_response,
    error_json_response,
    handle_serialization_errors,
)
from app.services import IssueService

issues_bp = Blueprint("issues", __name__)

logger = logging.getLogger(__name__)


@issues_bp.route("/issues", methods=["POST"])
@handle_serialization_errors
def create_issue():
    """
    이슈 생성 API
    ---
    tags:
      - Issues
    summary: 새로운 이슈 생성
    description: |
      새로운 이슈를 생성합니다. 생성 후 Slack 알림이 자동으로 전송됩니다.
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/issues', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          content: '시스템 로그인이 안 되는 문제가 있습니다.',
          training_course: '데이터 분석 스쿨 4기',
          username: '홍길동',
          date: '2025-01-15'
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
            - issue
            - training_course
            - username
          properties:
            issue:
              type: string
              description: 이슈 내용
              example: "시스템 로그인이 안 되는 문제가 있습니다."
            training_course:
              type: string
              description: 교육 과정명
              example: "데이터 분석 스쿨 4기"
            username:
              type: string
              description: 작성자명
              example: "홍길동"
            date:
              type: string
              description: 이슈 발생 날짜 (선택사항)
              example: "2025-01-15"
    responses:
      201:
        description: 이슈 생성 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "이슈가 성공적으로 생성되었습니다."
            data:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                content:
                  type: string
                  example: "시스템 로그인이 안 되는 문제가 있습니다."
                training_course:
                  type: string
                  example: "데이터 분석 스쿨 4기"
                username:
                  type: string
                  example: "홍길동"
                created_by:
                  type: string
                  example: "홍길동"
                date:
                  type: string
                  format: date
                  example: "2025-01-15"
                created_at:
                  type: string
                  format: date-time
                  example: "2025-01-15T10:30:00"
                resolved:
                  type: boolean
                  example: false
        examples:
          application/json:
            summary: 이슈 생성 성공 응답
            value:
              success: true
              message: "이슈가 성공적으로 생성되었습니다."
              data:
                id: 1
                content: "시스템 로그인이 안 되는 문제가 있습니다."
                training_course: "데이터 분석 스쿨 4기"
                username: "홍길동"
                created_by: "홍길동"
                date: "2025-01-15"
                created_at: "2025-01-15T10:30:00"
                resolved: false
      400:
        description: 필수 필드 누락
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "이슈 내용, 교육 과정, 작성자는 필수 입력 항목입니다."
            details:
              type: object
              example: null
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
              example: "이슈 생성 중 오류가 발생했습니다."
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 500
    """
    try:
        validated_data = IssueSerializer.deserialize_issue_create(request.json)
        issue_data = IssueService.create_issue(validated_data)
        try:
            notifier = SlackNotifier()
            message = (
                f"*새로운 이슈가 등록되었습니다!*\n"
                f">*과정:* {issue_data.get('training_course')}\n"
                f">*내용:* {issue_data['content']}\n"
                f">*작성자:* {issue_data.get('username')}"
            )
            notifier.send_notification(message, "issue")
        except Exception as e:
            logger.error(f"Slack notification failed: {str(e)}")

        return json_response(
            data=issue_data,
            message="이슈가 성공적으로 생성되었습니다.",
            status_code=201,
        )

    except Exception as e:
        logger.error(f"Error creating issue: {str(e)}", exc_info=True)
        return error_json_response("이슈 생성 중 오류가 발생했습니다.", status_code=500)


@issues_bp.route("/issues", methods=["GET"])
def get_issues():
    """
    해결되지 않은 이슈 목록 조회 API
    ---
    tags:
      - Issues
    summary: 해결되지 않은 이슈 목록을 조회합니다
    description: |
      해결되지 않은 이슈들의 목록을 조회합니다.
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/issues', {
        method: 'GET',
        credentials: 'include'
      });
      
      const result = await response.json();
      console.log(result);
      ```
    responses:
      200:
        description: 해결되지 않은 이슈 목록 반환
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "이슈 목록 조회 성공"
            data:
              type: array
              items:
                type: object
                properties:
                  training_course:
                    type: string
                    example: "데이터 분석 스쿨 4기"
                  issues:
                    type: array
                    items:
                      type: object
                      properties:
                        id:
                          type: integer
                          example: 1
                        content:
                          type: string
                          example: "시스템 로그인이 안 되는 문제가 있습니다."
                        training_course:
                          type: string
                          example: "데이터 분석 스쿨 4기"
                        username:
                          type: string
                          example: "홍길동"
                        date:
                          type: string
                          format: date
                          example: "2025-01-15"
                        created_at:
                          type: string
                          format: date-time
                          example: "2025-01-15T10:30:00"
                        resolved:
                          type: boolean
                          example: false
                        comments:
                          type: array
                          items:
                            type: object
                            properties:
                              id:
                                type: integer
                                example: 1
                              comment:
                                type: string
                                example: "이 문제는 이미 확인했습니다."
                              created_by:
                                type: string
                                example: "관리자"
                              created_at:
                                type: string
                                format: date-time
                                example: "2025-01-15T11:00:00"
        examples:
          application/json:
            summary: 이슈 목록 조회 성공 응답
            value:
              success: true
              message: "이슈 목록 조회 성공"
              data:
                - training_course: "데이터 분석 스쿨 4기"
                  issues:
                    - id: 1
                      content: "시스템 로그인이 안 되는 문제가 있습니다."
                      training_course: "데이터 분석 스쿨 4기"
                      username: "홍길동"
                      date: "2025-01-15"
                      created_at: "2025-01-15T10:30:00"
                      resolved: false
                      comments:
                        - id: 1
                          comment: "이 문제는 이미 확인했습니다."
                          created_by: "관리자"
                          created_at: "2025-01-15T11:00:00"
                - training_course: "웹 개발 스쿨 3기"
                  issues:
                    - id: 2
                      content: "과제 제출 시스템 오류"
                      training_course: "웹 개발 스쿨 3기"
                      username: "김철수"
                      date: "2025-01-14"
                      created_at: "2025-01-14T15:20:00"
                      resolved: false
                      comments: []
      500:
        description: 이슈 목록 조회 실패
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "이슈 목록을 불러오는 중 오류 발생"
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 500
    """
    try:
        response_data = IssueService.get_unresolved_issues()

        return json_response(
            data=response_data, message="이슈 목록 조회 성공", status_code=200
        )

    except Exception as e:
        logger.error("Error retrieving issues", exc_info=True)
        return error_json_response("이슈 목록을 불러오는 중 오류 발생", status_code=500)


# 이슈에 대한 댓글 달기
@issues_bp.route("/issues/comments", methods=["POST"])
@handle_serialization_errors
def add_comment():
    """
    이슈 댓글 추가 API
    ---
    tags:
      - Issues
    summary: 이슈에 댓글 추가
    description: |
      특정 이슈에 댓글을 추가합니다. 댓글 등록 후 Slack 알림이 전송됩니다.
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/issues/comments', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          issue_id: 1,
          comment: '이 문제는 이미 확인했습니다. 곧 해결하겠습니다.',
          created_by: '관리자'
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
            - issue_id
            - comment
            - username
          properties:
            issue_id:
              type: integer
              description: 이슈 ID
              example: 1
            comment:
              type: string
              description: 댓글 내용
              example: "이 문제는 이미 확인했습니다. 곧 해결하겠습니다."
            username:
              type: string
              description: 작성자명
              example: "관리자"
    responses:
      201:
        description: 댓글 추가 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "댓글이 등록되었습니다."
            data:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                issue_id:
                  type: integer
                  example: 1
                comment:
                  type: string
                  example: "이 문제는 이미 확인했습니다. 곧 해결하겠습니다."
                created_by:
                  type: string
                  example: "관리자"
                created_at:
                  type: string
                  format: date-time
                  example: "2025-01-15T11:00:00"
        examples:
          application/json:
            summary: 댓글 추가 성공 응답
            value:
              success: true
              message: "댓글이 등록되었습니다."
              data:
                id: 1
                issue_id: 1
                comment: "이 문제는 이미 확인했습니다. 곧 해결하겠습니다."
                created_by: "관리자"
                created_at: "2025-01-15T11:00:00"
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
              example: "이슈 ID, 댓글 내용, 작성자는 필수 입력 항목입니다."
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 400
      404:
        description: 이슈를 찾을 수 없음
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "해당 이슈를 찾을 수 없습니다."
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 404
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
              example: "댓글 등록 실패"
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 500
    """
    try:
        validated_data = IssueSerializer.deserialize_issue_comment_create(request.json)
        comment = IssueService.add_comment(validated_data)
        serialized_comment = IssueSerializer.serialize_issue_comment(comment)

        # 댓글 등록 알림
        notifier = SlackNotifier()
        notification_message = f"이슈에 새로운 댓글이 등록되었습니다!\n댓글: {serialized_comment['comment']}"
        notifier.send_notification(notification_message, channel_type="comment")

        return json_response(
            data=serialized_comment, message="댓글이 등록되었습니다.", status_code=201
        )
    except Exception as e:
        logger.error(f"댓글 등록 중 오류: {str(e)}")
        return error_json_response("댓글 등록 실패", status_code=500)


# 이슈에 대한 댓글 조회
@issues_bp.route("/issues/comments", methods=["GET"])
def get_issue_comments():
    """
    이슈사항의 댓글 조회 API
    ---
    tags:
      - Issues
    summary: 특정 이슈에 대한 댓글 목록을 조회합니다
    description: |
      특정 이슈에 등록된 댓글들의 목록을 조회합니다.
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/issues/comments?issue_id=1', {
        method: 'GET',
        credentials: 'include'
      });
      
      const result = await response.json();
      console.log(result);
      ```
    parameters:
      - name: issue_id
        in: query
        type: integer
        required: true
        description: "조회할 이슈 ID"
        example: 1
    responses:
      200:
        description: 이슈사항의 댓글 목록 반환
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "댓글 조회 성공"
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  issue_id:
                    type: integer
                    example: 1
                  comment:
                    type: string
                    example: "이 문제는 이미 확인했습니다. 곧 해결하겠습니다."
                  created_by:
                    type: string
                    example: "관리자"
                  created_at:
                    type: string
                    format: date-time
                    example: "2025-01-15T11:00:00"
        examples:
          application/json:
            summary: 댓글 목록 조회 성공 응답
            value:
              success: true
              message: "댓글 조회 성공"
              data:
                - id: 1
                  issue_id: 1
                  comment: "이 문제는 이미 확인했습니다. 곧 해결하겠습니다."
                  created_by: "관리자"
                  created_at: "2025-01-15T11:00:00"
                - id: 2
                  issue_id: 1
                  comment: "해결되었습니다. 확인해보세요."
                  created_by: "시스템관리자"
                  created_at: "2025-01-15T14:30:00"
      500:
        description: 댓글 조회 실패
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "댓글 조회 실패"
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 500
    """
    try:
        validated_data = IssueSerializer.deserialize_issue_comment_get(request.args)
        comments = IssueService.get_issue_comments(validated_data)
        serialized_comments = IssueSerializer.serialize_issue_comments(comments)

        return json_response(
            data=serialized_comments, message="댓글 조회 성공", status_code=200
        )

    except Exception as e:
        logger.error("Error retrieving issue comments", exc_info=True)
        return error_json_response("댓글 조회 실패", status_code=500)


@issues_bp.route("/issues/resolve", methods=["POST"])
@handle_serialization_errors
def resolve_issue():
    """
    이슈 해결 API
    ---
    tags:
      - Issues
    summary: 이슈 해결 처리
    description: |
      이슈를 해결된 상태로 변경합니다.
      
      ### API 명세
      **POST** `/issues/resolve`
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/issues/resolve', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          issue_id: 1
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
            - issue_id
          properties:
            issue_id:
              type: integer
              description: 해결할 이슈 ID
              example: 1
    responses:
      200:
        description: 이슈 해결 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "이슈가 성공적으로 해결되었습니다."
        examples:
          application/json:
            summary: 이슈 해결 성공 응답
            value:
              success: true
              message: "이슈가 성공적으로 해결되었습니다."
    """
    try:
        validated_data = IssueSerializer.deserialize_issue_resolve(request.json)
        issue = IssueService.resolve_issue(validated_data)
        serialized_issue = IssueSerializer.serialize_issue(issue)

        return json_response(
            data=serialized_issue, message="이슈가 해결되었습니다.", status_code=200
        )
    except Exception as e:
        logger.error("Error resolving issue", exc_info=True)
        return error_json_response("이슈 해결 실패", status_code=500)


# 이슈사항 전체 다운로드
@issues_bp.route("/issues/download", methods=["GET"])
def download_issues():
    """
    이슈사항을 Excel 파일로 다운로드하는 API
    ---
    tags:
      - Issues
    summary: 모든 이슈사항을 Excel 파일로 다운로드
    description: |
      모든 이슈사항을 Excel 파일로 다운로드합니다.
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/issues/download', {
        method: 'GET',
        credentials: 'include'
      });
      
      // 파일 다운로드 처리
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = '이슈사항.xlsx';
      a.click();
      ```
    responses:
      200:
        description: 이슈사항을 Excel 파일로 다운로드
        schema:
          type: file
          format: binary
        headers:
          Content-Disposition:
            description: 파일 다운로드 헤더
            schema:
              type: string
              example: "attachment; filename=이슈사항.xlsx"
          Content-Type:
            description: Excel 파일 타입
            schema:
              type: string
              example: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      500:
        description: 이슈사항 다운로드 실패
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "이슈 다운로드 실패"
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 500
    """
    try:
        all_issues = IssueService.get_all_issues()
        serialized_issues = IssueSerializer.serialize_issues(all_issues)

        # Excel 생성을 위한 데이터 변환
        issues = [
            (
                issue["id"],
                issue["content"],
                issue.get("date"),
                issue["training_course"],
                issue["created_at"],
                issue["resolved"],
            )
            for issue in serialized_issues
        ]

        # DataFrame 생성
        columns = ["ID", "이슈 내용", "날짜", "훈련 과정", "생성일", "해결됨"]
        df = pd.DataFrame(issues, columns=columns)

        # Excel 파일 생성
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="이슈사항")
        output.seek(0)

        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name="이슈사항.xlsx",
        )
    except Exception as e:
        logger.error("이슈사항 다운로드 실패", exc_info=True)
        return error_json_response("이슈 다운로드 실패", status_code=500)


# @issues_bp.route('/remarks', methods=['POST'])
# def save_remarks():
#     """
#     전달사항 저장 API
#     ---
#     tags:
#       - Remarks
#     parameters:
#       - in: body
#         name: body
#         description: 저장할 전달사항 데이터
#         required: true
#         schema:
#           type: object
#           required:
#             - remarks
#           properties:
#             remarks:
#               type: string
#               example: "전달사항 내용 예시"
#     responses:
#       201:
#         description: 전달사항 저장 성공
#       400:
#         description: 전달사항 데이터 누락
#       500:
#         description: 전달사항 저장 실패
#     """
#     try:
#         data = request.json
#         remarks = data.get('remarks')
#         if not remarks:
#             return jsonify({"success": False, "message": "Remarks are required"}), 400

#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute('''
#             INSERT INTO notices (type, title, content, date)
#             VALUES (%s, %s, %s, %s)
#         ''', ("전달사항", "전달사항 제목", remarks, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
#         conn.commit()
#         cursor.close()
#         conn.close()

#         return jsonify({"success": True, "message": "Remarks saved!"}), 201
#     except Exception as e:
#         logging.error("Error saving remarks", exc_info=True)
#         return jsonify({"success": False, "message": "Failed to save remarks"}), 500
