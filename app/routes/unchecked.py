from flask import Blueprint, request, jsonify
from app.database import get_db_connection
import logging
from datetime import datetime

bp = Blueprint('unchecked', __name__)

@bp.route('/unchecked_descriptions', methods=['GET'])
def get_unchecked_descriptions():
    """
    미체크 항목 설명 및 액션 플랜 조회 API
    ---
    tags:
      - Unchecked Descriptions
    summary: 미체크 항목 설명 및 액션 플랜 조회
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT ud.id, ud.content, ud.action_plan, ud.training_course, 
                   ti.dept, ud.created_at, ud.resolved, ud.id_task
            FROM unchecked_descriptions ud
            JOIN training_info ti ON ud.training_course = ti.training_course
            WHERE ud.resolved = FALSE  
            ORDER BY ud.created_at DESC;
        ''')
        unchecked_items = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": [
                {
                    "id": row[0],
                    "content": row[1],
                    "action_plan": row[2],
                    "training_course": row[3],
                    "dept": row[4],
                    "created_at": row[5],
                    "resolved": row[6],
                    "task_checklist_id": row[7]
                } for row in unchecked_items
            ]
        }), 200
    except Exception as e:
        logging.error("Error retrieving unchecked descriptions", exc_info=True)
        return jsonify({"success": False, "message": "미체크 항목 목록을 불러오는 중 오류 발생"}), 500

@bp.route('/unchecked_descriptions', methods=['POST'])
def save_unchecked_description():
    """
    미체크 항목 설명과 액션 플랜 저장 API
    ---
    tags:
      - Unchecked Descriptions
    summary: 미체크 항목 설명 및 액션 플랜 저장
    """
    try:
        if not request.is_json:
            return jsonify({"success": False, "message": "Invalid JSON format"}), 400

        data = request.get_json()
        description = data.get("description", "").strip()
        action_plan = data.get("action_plan", "").strip()
        training_course = data.get("training_course", "").strip()
        task_checklist_id = data.get("task_checklist_id")

        if not description or not action_plan or not training_course or not task_checklist_id:
            return jsonify({"success": False, "message": "필수 항목이 누락되었습니다."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO unchecked_descriptions 
            (content, action_plan, training_course, created_at, resolved, id_task)
            VALUES (%s, %s, %s, NOW(), FALSE, %s)
        ''', (description, action_plan, training_course, task_checklist_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "미체크 항목과 액션 플랜이 저장되었습니다!"}), 201

    except Exception as e:
        logging.error("Error saving unchecked description", exc_info=True)
        return jsonify({"success": False, "message": "서버 오류 발생"}), 500

@bp.route('/unchecked_comments', methods=['POST'])
def add_unchecked_comment():
    """
    미체크 항목에 댓글 추가 API
    ---
    tags:
      - Unchecked Comments
    summary: 미체크 항목에 대한 댓글을 저장합니다.
    """
    try:
        data = request.json
        unchecked_id = data.get('unchecked_id')
        comment = data.get('comment')

        if not unchecked_id or not comment:
            return jsonify({"success": False, "message": "미체크 항목 ID와 댓글을 입력하세요."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO unchecked_comments (unchecked_id, comment, created_at) VALUES (%s, %s, NOW())",
            (unchecked_id, comment)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "댓글이 저장되었습니다."}), 201
    except Exception as e:
        logging.error("Error saving unchecked comment", exc_info=True)
        return jsonify({"success": False, "message": "댓글 저장 실패"}), 500

@bp.route('/unchecked_descriptions/resolve', methods=['POST'])
def resolve_unchecked_description():
    """
    미체크 항목 해결 API
    ---
    tags:
      - Unchecked Descriptions
    summary: 특정 미체크 항목을 해결 상태로 변경하고 관련 task를 체크 상태로 업데이트합니다.
    """
    try:
        data = request.json
        unchecked_id = data.get('unchecked_id')

        if not unchecked_id:
            return jsonify({"success": False, "message": "미체크 항목 ID가 필요합니다."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # 트랜잭션 시작
            cursor.execute("BEGIN")

            # 1. 미체크 항목 정보와 연결된 task_checklist id 조회
            cursor.execute("""
                SELECT id_task
                FROM unchecked_descriptions 
                WHERE id = %s
            """, (unchecked_id,))
            
            unchecked_item = cursor.fetchone()
            if not unchecked_item:
                cursor.execute("ROLLBACK")
                return jsonify({"success": False, "message": "해당 미체크 항목을 찾을 수 없습니다."}), 404

            task_checklist_id = unchecked_item[0]

            # 2. task_checklist 업데이트
            cursor.execute("""
                UPDATE task_checklist
                SET is_checked = TRUE
                WHERE id = %s
            """, (task_checklist_id,))

            # 3. 미체크 항목을 해결 상태로 변경
            cursor.execute("""
                UPDATE unchecked_descriptions 
                SET resolved = TRUE,
                    resolved_at = NOW()
                WHERE id = %s
            """, (unchecked_id,))

            # 트랜잭션 커밋
            cursor.execute("COMMIT")

            return jsonify({
                "success": True, 
                "message": "미체크 항목이 해결되었으며, 체크 상태가 업데이트되었습니다."
            }), 200

        except Exception as e:
            # 오류 발생 시 롤백
            cursor.execute("ROLLBACK")
            raise e

    except Exception as e:
        logging.error("Error resolving unchecked description", exc_info=True)
        return jsonify({"success": False, "message": "미체크 항목 해결 실패"}), 500

    finally:
        cursor.close()
        conn.close()

@bp.route('/unchecked_comments', methods=['GET'])
def get_unchecked_comments():
    """
    미체크 항목의 댓글 조회 API
    ---
    tags:
      - Unchecked Comments
    summary: "특정 미체크 항목의 댓글 목록을 조회합니다."
    """
    try:
        unchecked_id = request.args.get('unchecked_id')

        if not unchecked_id:
            return jsonify({"success": False, "message": "미체크 항목 ID를 입력하세요."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, comment, created_at FROM unchecked_comments WHERE unchecked_id = %s ORDER BY created_at ASC",
            (unchecked_id,)
        )
        comments = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": [{"id": row[0], "comment": row[1], "created_at": row[2]} for row in comments]
        }), 200
    except Exception as e:
        logging.error("Error retrieving unchecked comments", exc_info=True)
        return jsonify({"success": False, "message": "미체크 항목 댓글 조회 실패"}), 500 