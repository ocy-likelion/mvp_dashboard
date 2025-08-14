from flask import Blueprint, request, jsonify, send_file
import io
import pandas as pd
import logging
from app.models.db import get_db_session
from app.models.models import Issue, IssueComment
from app.utils.notifications import SlackNotifier
from datetime import datetime

issues_bp = Blueprint("issues", __name__)

logger = logging.getLogger(__name__)


@issues_bp.route("/issues", methods=["POST"])
def create_issue():
    """
    이슈 생성 API
    ---
    tags:
      - Issues
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
            training_course:
              type: string
              description: 교육 과정명
            username:
              type: string
              description: 작성자명
            date:
              type: string
              description: 이슈 발생 날짜 (선택사항)
    responses:
      201:
        description: 이슈 생성 성공
      400:
        description: 필수 필드 누락
      500:
        description: 서버 오류
    """
    try:
        data = request.json
        logger.info(f"Received issue data: {data}")

        # 1. 필수 필드 검사
        required_fields = ["issue", "training_course", "username"]
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            logger.error(f"Missing required fields: {missing_fields}")
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"필수 필드가 누락되었습니다: {', '.join(missing_fields)}",
                    }
                ),
                400,
            )

        # 2. 기본값 설정
        issue_data = {
            "content": data["issue"],
            "training_course": data["training_course"],
            "username": data["username"],
            "created_by": data["username"],  # username과 동일하게 설정
            "date": data.get("date"),
            "resolved": False,  # 기본값 False
        }

        # 3. 데이터베이스 저장 - ORM 사용
        session = get_db_session()
        try:
            # 이슈 생성
            issue = Issue(
                content=issue_data["content"],
                training_course=issue_data["training_course"],
                username=issue_data["username"],
                created_by=issue_data["created_by"],
                date=issue_data["date"],
                resolved=False,
            )

            session.add(issue)
            session.commit()

            issue_id = issue.id

        except Exception as e:
            session.rollback()
            logger.error(f"이슈 생성 중 오류: {str(e)}")
            return (
                jsonify(
                    {"success": False, "message": "이슈 생성 중 오류가 발생했습니다."}
                ),
                500,
            )
        finally:
            session.close()

        # 4. Slack 알림 전송
        try:
            notifier = SlackNotifier()
            message = (
                f"*새로운 이슈가 등록되었습니다!*\n"
                f">*과정:* {issue_data['training_course']}\n"
                f">*내용:* {issue_data['content']}\n"
                f">*작성자:* {issue_data['username']}"
            )
            notifier.send_notification(message, "issue")
        except Exception as e:
            logger.error(f"Slack notification failed: {str(e)}")

        # 5. 성공 응답
        return (
            jsonify(
                {
                    "success": True,
                    "message": "이슈가 성공적으로 생성되었습니다.",
                    "data": {"id": issue_id, **issue_data},
                }
            ),
            201,
        )

    except Exception as e:
        logger.error(f"Error creating issue: {str(e)}", exc_info=True)
        return (
            jsonify({"success": False, "message": "이슈 생성 중 오류가 발생했습니다."}),
            500,
        )


@issues_bp.route("/issues", methods=["GET"])
def get_issues():
    """
    해결되지 않은 이슈 목록 조회 API
    ---
    tags:
      - Issues
    summary: "해결되지 않은 이슈 목록을 조회합니다."
    responses:
      200:
        description: 해결되지 않은 이슈 목록 반환
      500:
        description: 이슈 목록 조회 실패
    """
    try:
        session = get_db_session()
        
        # ORM을 사용하여 해결되지 않은 이슈 조회
        issues_query = session.query(Issue).filter(Issue.resolved == False).order_by(Issue.created_at.desc())
        issues = issues_query.all()
        
        # 교육과정별로 그룹화
        issues_grouped = {}
        for issue in issues:
            course = issue.training_course
            if course not in issues_grouped:
                issues_grouped[course] = []
            
            # 댓글 조회
            comments = session.query(IssueComment).filter(IssueComment.issue_id == issue.id).all()
            comments_data = [
                {
                    'id': comment.id,
                    'comment': comment.comment,
                    'created_at': comment.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    'created_by': comment.created_by or '작성자 없음'
                }
                for comment in comments
            ]
            
            issue_data = {
                'id': issue.id,
                'content': issue.content,
                'date': issue.date.strftime("%Y-%m-%d") if issue.date else None,
                'created_at': issue.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                'created_by': issue.created_by or '작성자 없음',
                'resolved': issue.resolved,
                'comments': comments_data
            }
            issues_grouped[course].append(issue_data)
        
        session.close()
        
        # 응답 형식 변환
        response_data = [
            {"training_course": course, "issues": issues_list}
            for course, issues_list in issues_grouped.items()
        ]
        
        return jsonify({"success": True, "data": response_data}), 200
        
    except Exception as e:
        logger.error("Error retrieving issues", exc_info=True)
        return (
            jsonify({"success": False, "message": "이슈 목록을 불러오는 중 오류 발생"}),
            500,
        )


# 이슈에 대한 댓글 달기
@issues_bp.route("/issues/comments", methods=["POST"])
def add_comment():
    """
    이슈 댓글 추가 API
    ---
    tags:
      - Issues
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
            comment:
              type: string
              description: 댓글 내용
            username:
              type: string
              description: 작성자명
    responses:
      201:
        description: 댓글 추가 성공
      400:
        description: 필수 데이터 누락
      404:
        description: 이슈를 찾을 수 없음
      500:
        description: 서버 오류
    """
    try:
        data = request.json
        issue_id = data.get("issue_id")
        comment = data.get("comment")
        created_by = data.get("username")

        if not all([issue_id, comment, created_by]):
            return (
                jsonify({"success": False, "message": "필수 데이터가 누락되었습니다."}),
                400,
            )

        session = get_db_session()
        try:
            # 이슈 정보 조회
            issue = session.query(Issue).filter(Issue.id == issue_id).first()

            if not issue:
                return (
                    jsonify({"success": False, "message": "해당 이슈를 찾을 수 없습니다."}),
                    404,
                )

            # 댓글 저장
            issue_comment = IssueComment(
                issue_id=issue_id,
                comment=comment,
                created_by=created_by,
            )

            session.add(issue_comment)
            session.commit()

        except Exception as e:
            session.rollback()
            logger.error(f"댓글 등록 중 오류: {str(e)}")
            return jsonify({"success": False, "message": "댓글 등록 실패"}), 500
        finally:
            session.close()

        # 댓글 등록 알림
        notifier = SlackNotifier()
        notification_message = f"이슈에 새로운 댓글이 등록되었습니다!\n과정명: {issue.training_course}\n댓글: {comment}"
        notifier.send_notification(notification_message, channel_type="comment")

        return jsonify({"success": True, "message": "댓글이 등록되었습니다."}), 201
    except Exception as e:
        logger.error(f"댓글 등록 중 오류: {str(e)}")
        return jsonify({"success": False, "message": "댓글 등록 실패"}), 500


# 이슈에 대한 댓글 조회
@issues_bp.route("/issues/comments", methods=["GET"])
def get_issue_comments():
    """
    이슈사항의 댓글 조회 API
    ---
    tags:
      - Issues
    summary: "특정 이슈에 대한 댓글 목록을 조회합니다."
    parameters:
      - name: issue_id
        in: query
        type: integer
        required: true
        description: "조회할 이슈 ID"
    responses:
      200:
        description: 이슈사항의 댓글 목록 반환
      500:
        description: 댓글 조회 실패
    """
    try:
        issue_id = request.args.get("issue_id")

        if not issue_id:
            return jsonify({"success": False, "message": "이슈 ID를 입력하세요."}), 400

        session = get_db_session()
        try:
            comments_query = session.query(IssueComment).filter(
                IssueComment.issue_id == issue_id
            ).order_by(IssueComment.created_at.asc())
            
            comments = comments_query.all()
            
            comments_data = [
                {
                    "id": comment.id,
                    "comment": comment.comment,
                    "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "created_by": comment.created_by or "작성자 없음",
                }
                for comment in comments
            ]
            
            return jsonify({"success": True, "data": comments_data}), 200
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error("Error retrieving issue comments", exc_info=True)
        return jsonify({"success": False, "message": "댓글 조회 실패"}), 500


# 해결된 이슈 클릭
@issues_bp.route("/issues/resolve", methods=["POST"])
def resolve_issue():
    """
    이슈 해결 API
    ---
    tags:
      - Issues
    summary: "특정 이슈를 해결 처리합니다."
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            issue_id:
              type: integer
              example: 1
    responses:
      200:
        description: 이슈 해결 성공
      400:
        description: 요청 데이터 오류
      500:
        description: 이슈 해결 실패
    """
    try:
        data = request.json
        issue_id = data.get("issue_id")

        if not issue_id:
            return jsonify({"success": False, "message": "이슈 ID가 필요합니다."}), 400

        session = get_db_session()
        try:
            issue = session.query(Issue).filter(Issue.id == issue_id).first()
            if not issue:
                return jsonify({"success": False, "message": "이슈를 찾을 수 없습니다."}), 404
                
            issue.resolved = True
            session.commit()
            
        except Exception as e:
            session.rollback()
            logger.error(f"이슈 해결 중 오류: {str(e)}")
            return jsonify({"success": False, "message": "이슈 해결 실패"}), 500
        finally:
            session.close()

        return jsonify({"success": True, "message": "이슈가 해결되었습니다."}), 200
    except Exception as e:
        logger.error("Error resolving issue", exc_info=True)
        return jsonify({"success": False, "message": "이슈 해결 실패"}), 500


# 이슈사항 전체 다운로드
@issues_bp.route("/issues/download", methods=["GET"])
def download_issues():
    """
    이슈사항을 Excel 파일로 다운로드하는 API
    ---
    tags:
      - Issues
    responses:
      200:
        description: 이슈사항을 Excel 파일로 다운로드
      500:
        description: 이슈사항 다운로드 실패
    """
    try:
        session = get_db_session()
        
        issues_query = session.query(Issue).all()
        issues = [
            (
                issue.id,
                issue.content,
                issue.date.strftime("%Y-%m-%d") if issue.date else None,
                issue.training_course,
                issue.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                issue.resolved
            )
            for issue in issues_query
        ]
        
        session.close()

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
        return jsonify({"success": False, "message": "이슈 다운로드 실패"}), 500


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
