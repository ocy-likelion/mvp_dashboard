from flask import Blueprint, request, jsonify, send_file
import io
import pandas as pd
import logging
from app.models.db import get_db_connection

issues_bp = Blueprint('issues', __name__)

@issues_bp.route('/issues', methods=['POST'])
def save_issue():
    """
    이슈사항 저장 API
    ---
    tags:
      - Issues
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            issue:
              type: string
              example: "강의 자료 오류 발생"
    responses:
      201:
        description: 이슈사항 저장 성공
      400:
        description: 요청 데이터 오류
      500:
        description: 서버 오류
    """
    try:
        data = request.json
        issue_text = data.get('issue')
        training_course = data.get('training_course')
        date = data.get('date')
        created_by = data.get('username')  # 프론트엔드에서 전달한 username 사용

        if not issue_text or not training_course or not date or not created_by:
            return jsonify({"success": False, "message": "이슈, 훈련 과정, 날짜, 작성자를 모두 입력하세요."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            INSERT INTO issues (content, date, training_course, created_at, resolved, created_by)
            VALUES (%s, %s, %s, NOW(), FALSE, %s)
        '''
        cursor.execute(query, (issue_text, date, training_course, created_by))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "이슈가 저장되었습니다."}), 201
    except Exception as e:
        logging.error("Error saving issue", exc_info=True)
        return jsonify({"success": False, "message": "이슈 저장 실패"}), 500


@issues_bp.route('/issues', methods=['GET'])
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
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT training_course, json_agg(json_build_object(
                'id', i.id, 
                'content', i.content, 
                'date', i.date, 
                'created_at', i.created_at,
                'created_by', COALESCE(i.created_by, '작성자 없음'),
                'resolved', i.resolved,
                'comments', (
                    SELECT json_agg(json_build_object(
                        'id', ic.id, 
                        'comment', ic.comment,
                        'created_at', ic.created_at,
                        'created_by', COALESCE(ic.created_by, '작성자 없음')
                    )) FROM issue_comments ic WHERE ic.issue_id = i.id
                )
            )) AS issues
            FROM issues i
            WHERE i.resolved = FALSE  
            GROUP BY training_course
            ORDER BY MIN(i.created_at) DESC;
        ''')
        issues_grouped = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": [
                {"training_course": row[0], "issues": row[1]} for row in issues_grouped
            ]
        }), 200
    except Exception as e:
        logging.error("Error retrieving issues", exc_info=True)
        return jsonify({"success": False, "message": "이슈 목록을 불러오는 중 오류 발생"}), 500


# 이슈에 대한 댓글 달기
@issues_bp.route('/issues/comments', methods=['POST'])
def add_issue_comment():
    """
    이슈사항에 대한 댓글 저장 API
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
              example: 1
            comment:
              type: string
              example: "이슈에 대한 답변입니다."
            username:
              type: string
              example: "홍길동"
    responses:
      201:
        description: 댓글 저장 성공
      400:
        description: 요청 데이터 오류
      500:
        description: 서버 오류 발생
    """
    try:
        data = request.json
        issue_id = data.get('issue_id')
        comment = data.get('comment')
        created_by = data.get('username')  # 프론트엔드에서 전달받은 username 사용

        if not issue_id or not comment or not created_by:
            return jsonify({"success": False, "message": "이슈 ID, 댓글 내용, 작성자 정보를 모두 입력하세요."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO issue_comments (issue_id, comment, created_at, created_by) VALUES (%s, %s, NOW(), %s)",
            (issue_id, comment, created_by)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "댓글이 저장되었습니다."}), 201
    except Exception as e:
        logging.error("Error saving issue comment", exc_info=True)
        return jsonify({"success": False, "message": "댓글 저장 실패"}), 500

# 이슈에 대한 댓글 조회
@issues_bp.route('/issues/comments', methods=['GET'])
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
        issue_id = request.args.get('issue_id')

        if not issue_id:
            return jsonify({"success": False, "message": "이슈 ID를 입력하세요."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, comment, created_at, created_by FROM issue_comments WHERE issue_id = %s ORDER BY created_at ASC",
            (issue_id,)
        )
        comments = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": [
                {
                    "id": row[0], 
                    "comment": row[1], 
                    "created_at": row[2],
                    "created_by": row[3] if row[3] else "작성자 없음"  # created_by가 NULL인 경우 처리
                } for row in comments
            ]
        }), 200
    except Exception as e:
        logging.error("Error retrieving issue comments", exc_info=True)
        return jsonify({"success": False, "message": "댓글 조회 실패"}), 500

# 해결된 이슈 클릭
@issues_bp.route('/issues/resolve', methods=['POST'])
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
        issue_id = data.get('issue_id')

        if not issue_id:
            return jsonify({"success": False, "message": "이슈 ID가 필요합니다."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE issues SET resolved = TRUE WHERE id = %s",
            (issue_id,)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "이슈가 해결되었습니다."}), 200
    except Exception as e:
        logging.error("Error resolving issue", exc_info=True)
        return jsonify({"success": False, "message": "이슈 해결 실패"}), 500

# 이슈사항 전체 다운로드
@issues_bp.route('/issues/download', methods=['GET'])
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
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, content, date, training_course, created_at, resolved FROM issues")
        issues = cursor.fetchall()
        cursor.close()
        conn.close()

        # DataFrame 생성
        columns = ["ID", "이슈 내용", "날짜", "훈련 과정", "생성일", "해결됨"]
        df = pd.DataFrame(issues, columns=columns)

        # Excel 파일 생성
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name="이슈사항")
        output.seek(0)

        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name="이슈사항.xlsx"
        )
    except Exception as e:
        logging.error("이슈사항 다운로드 실패", exc_info=True)
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