from flask import Blueprint, request, jsonify
from app.database import get_db_connection
import logging

bp = Blueprint('training', __name__)

@bp.route('/training_courses', methods=['GET'])
def get_training_courses():
    """
    training_info 테이블에서 training_course 목록을 가져오는 API
    ---
    tags:
      - Training Info
    responses:
      200:
        description: 훈련과정 목록 반환
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT training_course FROM training_info ORDER BY start_date DESC")
        courses = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": [course[0] for course in courses]
        }), 200
    except Exception as e:
        logging.error("Error fetching training courses", exc_info=True)
        return jsonify({"success": False, "message": "Failed to fetch training courses"}), 500

@bp.route('/training_info', methods=['POST'])
def save_training_info():
    """
    훈련 과정 정보 저장 API
    ---
    tags:
      - Training Info
    """
    try:
        data = request.json
        training_course = data.get("training_course", "").strip()
        start_date = data.get("start_date", "").strip()
        end_date = data.get("end_date", "").strip()
        dept = data.get("dept", "").strip()

        if not training_course or not start_date or not end_date or not dept:
            return jsonify({"success": False, "message": "모든 필드를 입력하세요."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO training_info (training_course, start_date, end_date, dept)
            VALUES (%s, %s, %s, %s)
        ''', (training_course, start_date, end_date, dept))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "훈련 과정이 저장되었습니다!"}), 201
    except Exception as e:
        logging.error("Error saving training info", exc_info=True)
        return jsonify({"success": False, "message": "Failed to save training info"}), 500

@bp.route('/training_info', methods=['GET'])
def get_training_info():
    """
    훈련 과정 목록 조회 API
    ---
    tags:
      - Training Info
    responses:
      200:
        description: 저장된 훈련 과정 목록 반환
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT training_course, start_date, end_date, dept FROM training_info ORDER BY start_date DESC')
        courses = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": [
                {
                    "training_course": row[0],
                    "start_date": row[1],
                    "end_date": row[2],
                    "dept": row[3]
                }
                for row in courses
            ]
        })
    except Exception as e:
        logging.error("Error fetching training info", exc_info=True)
        return jsonify({"success": False, "message": "Failed to fetch training info"}), 500 