from flask import Blueprint, request, jsonify
from app.database import get_db_connection
import logging

bp = Blueprint('irregular_tasks', __name__)

@bp.route('/irregular_tasks', methods=['GET'])
def get_irregular_tasks():
    """
    비정기 업무 체크리스트 조회 API
    ---
    tags:
      - Irregular Tasks
    summary: "비정기 업무 체크리스트의 가장 최근 상태를 조회합니다."
    responses:
      200:
        description: 비정기 업무 체크리스트 조회 성공
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT DISTINCT ON (task_name) id, task_name, is_checked, checked_date
            FROM irregular_tasks
            ORDER BY task_name, checked_date DESC
        ''')
        tasks = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": [{"id": t[0], "task_name": t[1], "is_checked": t[2], "checked_date": t[3]} for t in tasks]
        }), 200
    except Exception as e:
        logging.error("비정기 업무 조회 오류", exc_info=True)
        return jsonify({"success": False, "message": "비정기 업무 조회 실패"}), 500

@bp.route('/irregular_tasks', methods=['POST'])
def save_irregular_tasks():
    """
    비정기 업무 체크리스트 추가 저장 API
    ---
    tags:
      - Irregular Tasks
    summary: "비정기 업무 체크리스트 업데이트 데이터를 저장합니다."
    """
    try:
        data = request.json
        updates = data.get("updates")
        training_course = data.get("training_course")
        
        if not updates or not training_course:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for update in updates:
            task_name = update.get("task_name")
            is_checked = update.get("is_checked")
            cursor.execute('''
                INSERT INTO irregular_tasks (task_name, is_checked, checked_date, training_course)
                VALUES (%s, %s, NOW(), %s)
            ''', (task_name, is_checked, training_course))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "비정기 업무 체크리스트가 저장되었습니다!"}), 201
    except Exception as e:
        logging.error("비정기 업무 체크리스트 저장 오류", exc_info=True)
        return jsonify({"success": False, "message": "비정기 업무 체크리스트 저장 실패"}), 500 