from flask import Blueprint, request, jsonify, session
from app.database import get_db_connection
import logging

bp = Blueprint('tasks', __name__)

@bp.route('/tasks', methods=['GET'])
def get_tasks():
    """
    업무 체크리스트 조회 API
    ---
    tags:
      - Tasks
    summary: 업무 체크리스트 데이터 조회
    responses:
      200:
        description: 모든 업무 체크리스트 데이터를 반환함
    """
    try:
        task_category = request.args.get('task_category')

        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT id, task_name, task_period, task_category, guide FROM task_items"
        params = []

        if task_category:
            query += " WHERE task_category = %s"
            params.append(task_category)

        query += " ORDER BY id ASC"

        cursor.execute(query, tuple(params))

        tasks = [
            {
                "id": row[0],
                "task_name": row[1],
                "task_period": row[2],
                "task_category": row[3],
                "guide": row[4] if row[4] else "업무 가이드 없음"
            }
            for row in cursor.fetchall()
        ]

        cursor.close()
        conn.close()

        return jsonify({"success": True, "data": tasks}), 200
    except Exception as e:
        logging.error("Error retrieving tasks", exc_info=True)
        return jsonify({"success": False, "message": "Failed to retrieve tasks"}), 500

@bp.route('/tasks', methods=['POST'])
def save_tasks():
    """
    업무 체크리스트 저장 API
    ---
    tags:
      - Tasks
    summary: 업무 체크리스트 저장
    """
    if 'user' not in session:
        return jsonify({"success": False, "message": "로그인이 필요합니다."}), 401

    user_id = session['user']['username']

    data = request.json
    updates = data.get("updates")
    training_course = data.get("training_course")

    if not updates or not training_course:
        return jsonify({"success": False, "message": "No data provided"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        for update in updates:
            task_name = update.get("task_name")
            is_checked = update.get("is_checked", False)

            cursor.execute("SELECT id FROM task_items WHERE task_name = %s", (task_name,))
            task_item = cursor.fetchone()
            if not task_item:
                return jsonify({"success": False, "message": f"Task '{task_name}' does not exist"}), 400

            task_id = task_item[0]

            cursor.execute("""
                INSERT INTO task_checklist (task_id, training_course, is_checked, checked_date, username)
                VALUES (%s, %s, %s, NOW(), %s);
            """, (task_id, training_course, is_checked, user_id))

        conn.commit()
        return jsonify({"success": True, "message": "Tasks saved successfully!"}), 201

    except Exception as e:
        logging.error("Error saving tasks", exc_info=True)
        return jsonify({"success": False, "message": "Failed to save tasks"}), 500

    finally:
        cursor.close()
        conn.close() 