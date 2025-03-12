from flask import Blueprint, request, jsonify
from app.database import get_db_connection
from datetime import datetime
import logging

bp = Blueprint('notices', __name__)

@bp.route('/notices', methods=['GET'])
def get_notices():
    """
    공지사항 및 전달사항 조회 API
    ---
    tags:
      - Notices
    responses:
      200:
        description: 공지사항 및 전달사항 데이터를 포함한 응답
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM notices ORDER BY date DESC')
        notices = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": {
                "notices": notices,
                "remarks": [notice for notice in notices if notice[1] == '전달사항']
            }
        }), 200
    except Exception as e:
        logging.error("Error retrieving notices", exc_info=True)
        return jsonify({"success": False, "message": "Failed to retrieve notices"}), 500

@bp.route('/notices', methods=['POST'])
def add_notice():
    """
    공지사항 추가 API
    ---
    tags:
      - Notices
    summary: 새로운 공지사항을 추가합니다.
    """
    try:
        data = request.json
        title = data.get("title")
        content = data.get("content")

        if not title or not content:
            return jsonify({"success": False, "message": "제목과 내용을 입력하세요."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO notices (title, content, date)
            VALUES (%s, %s, %s)
        ''', (title, content, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "공지사항이 추가되었습니다."}), 201
    except Exception as e:
        logging.error("공지사항 추가 오류", exc_info=True)
        return jsonify({"success": False, "message": "공지사항 추가 실패"}), 500

@bp.route('/remarks', methods=['POST'])
def save_remarks():
    """
    전달사항 저장 API
    ---
    tags:
      - Remarks
    """
    try:
        data = request.json
        remarks = data.get('remarks')
        if not remarks:
            return jsonify({"success": False, "message": "Remarks are required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO notices (type, title, content, date)
            VALUES (%s, %s, %s, %s)
        ''', ("전달사항", "전달사항 제목", remarks, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Remarks saved!"}), 201
    except Exception as e:
        logging.error("Error saving remarks", exc_info=True)
        return jsonify({"success": False, "message": "Failed to save remarks"}), 500 