from flask import Blueprint, request, jsonify, send_file
from app.database import get_db_connection
import pandas as pd
import io
import logging

bp = Blueprint('issues', __name__)

@bp.route('/issues', methods=['GET'])
def get_issues():
    """
    해결되지 않은 이슈 목록 조회 API
    ---
    tags:
      - Issues
    summary: "해결되지 않은 이슈 목록을 조회합니다."
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
                'resolved', i.resolved,
                'comments', (
                    SELECT json_agg(json_build_object(
                        'id', ic.id, 
                        'comment', ic.comment, 
                        'created_at', ic.created_at
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

@bp.route('/issues', methods=['POST'])
def save_issue():
    """
    이슈사항 저장 API
    ---
    tags:
      - Issues
    """
    try:
        data = request.json
        issue_text = data.get('issue')
        training_course = data.get('training_course')
        date = data.get('date')

        if not issue_text or not training_course or not date:
            return jsonify({"success": False, "message": "이슈, 훈련 과정, 날짜를 모두 입력하세요."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO issues (content, date, training_course, created_at, resolved)
            VALUES (%s, %s, %s, NOW(), FALSE)
        ''', (issue_text, date, training_course))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "이슈가 저장되었습니다."}), 201
    except Exception as e:
        logging.error("Error saving issue", exc_info=True)
        return jsonify({"success": False, "message": "이슈 저장 실패"}), 500

@bp.route('/issues/comments', methods=['POST'])
def add_issue_comment():
    """
    이슈사항에 대한 댓글 저장 API
    ---
    tags:
      - Issues
    """
    try:
        data = request.json
        issue_id = data.get('issue_id')
        comment = data.get('comment')

        if not issue_id or not comment:
            return jsonify({"success": False, "message": "이슈 ID와 댓글 내용을 입력하세요."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO issue_comments (issue_id, comment, created_at) VALUES (%s, %s, NOW())",
            (issue_id, comment)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "댓글이 저장되었습니다."}), 201
    except Exception as e:
        logging.error("Error saving issue comment", exc_info=True)
        return jsonify({"success": False, "message": "댓글 저장 실패"}), 500

@bp.route('/issues/resolve', methods=['POST'])
def resolve_issue():
    """
    이슈 해결 API
    ---
    tags:
      - Issues
    summary: "특정 이슈를 해결 처리합니다."
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

@bp.route('/issues/download', methods=['GET'])
def download_issues():
    """
    이슈사항을 Excel 파일로 다운로드하는 API
    ---
    tags:
      - Issues
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, content, date, training_course, created_at, resolved FROM issues")
        issues = cursor.fetchall()
        cursor.close()
        conn.close()

        columns = ["ID", "이슈 내용", "날짜", "훈련 과정", "생성일", "해결됨"]
        df = pd.DataFrame(issues, columns=columns)

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