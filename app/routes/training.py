from flask import Blueprint, request, jsonify
import logging
from app.models.db import get_db_connection
from datetime import datetime

training_bp = Blueprint('training', __name__)

@training_bp.route('/training_courses', methods=['GET'])
def get_training_courses():
    """
    training_info 테이블에서 training_course 목록을 가져오는 API
    (현재 진행 중이거나 종료된 지 1주일 이내의 과정만 반환)
    ---
    tags:
      - Training Info
    responses:
      200:
        description: 유효한 훈련과정 목록 반환
      500:
        description: 훈련과정 목록 불러오기 실패
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 현재 날짜 기준으로 종료된 지 1주일 이내이거나 아직 진행 중인 과정만 조회
        cursor.execute('''
            SELECT training_course 
            FROM training_info 
            WHERE end_date >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY start_date DESC
        ''')
        
        courses = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": [course[0] for course in courses]
        }), 200
    except Exception as e:
        logging.error("Error fetching training courses", exc_info=True)
        return jsonify({"success": False, "message": "훈련 과정 목록을 불러오는데 실패했습니다."}), 500


@training_bp.route('/training_info', methods=['POST'])
def save_training_info():
    """
    훈련 과정 정보 저장 API
    ---
    tags:
      - Training Info
    parameters:
      - in: body
        name: body
        description: "훈련 과정 정보를 JSON 형식으로 전달"
        required: true
        schema:
          type: object
          required:
            - training_course
            - start_date
            - end_date
            - dept
            - manager_name
          properties:
            training_course:
              type: string
              example: "데이터 분석 스쿨 100기"
            start_date:
              type: string
              format: date
              example: "2025-01-02"
            end_date:
              type: string
              format: date
              example: "2025-06-01"
            dept:
              type: string
              example: "TechSol"
            manager_name:
              type: string
              example: "홍길동"
    responses:
      201:
        description: 훈련 과정 저장 성공
      400:
        description: 필수 필드 누락
      500:
        description: 훈련 과정 저장 실패
    """
    try:
        data = request.json
        training_course = data.get("training_course", "").strip()
        start_date = data.get("start_date", "").strip()
        end_date = data.get("end_date", "").strip()
        dept = data.get("dept", "").strip()
        manager_name = data.get("manager_name", "").strip()

        if not training_course or not start_date or not end_date or not dept or not manager_name:
            return jsonify({"success": False, "message": "모든 필드를 입력하세요."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO training_info (training_course, start_date, end_date, dept, manager_name)
            VALUES (%s, %s, %s, %s, %s)
        ''', (training_course, start_date, end_date, dept, manager_name))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "훈련 과정이 저장되었습니다!"}), 201
    except Exception as e:
        logging.error("Error saving training info", exc_info=True)
        return jsonify({"success": False, "message": "Failed to save training info"}), 500


@training_bp.route('/training_info', methods=['GET'])
def get_training_info():
    """
    훈련 과정 목록 조회 API
    ---
    tags:
      - Training Info
    responses:
      200:
        description: 저장된 훈련 과정 목록 반환
      500:
        description: 훈련 과정 목록 조회 실패
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
                {"training_course": row[0], "start_date": row[1], "end_date": row[2], "dept": row[3]}
                for row in courses
            ]
        })
    except Exception as e:
        logging.error("Error fetching training info", exc_info=True)
        return jsonify({"success": False, "message": "Failed to fetch training info"}), 500


@training_bp.route('/unchecked_descriptions', methods=['GET'])
def get_unchecked_descriptions():
    """
    미체크 항목 설명 및 액션 플랜 조회 API (부서명 포함)
    ---
    tags:
      - Unchecked Descriptions
    responses:
      200:
        description: 미체크 항목 목록 조회 성공
      500:
        description: 미체크 항목 목록 조회 실패
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                ud.id, 
                ud.content, 
                ud.action_plan, 
                ud.training_course, 
                ti.dept, 
                ud.created_at, 
                ud.resolved,
                COALESCE(ti2.due, 3) as due,  -- due가 없으면 기본값 3일
                (ud.created_at + (COALESCE(ti2.due, 3) || ' days')::interval)::date as deadline,
                CASE 
                    WHEN CURRENT_DATE > (ud.created_at + (COALESCE(ti2.due, 3) || ' days')::interval)::date 
                    THEN TRUE 
                    ELSE FALSE 
                END as is_overdue
            FROM unchecked_descriptions ud
            JOIN training_info ti ON ud.training_course = ti.training_course
            LEFT JOIN task_items ti2 ON ud.content LIKE ti2.task_name || '%에 대한 미체크 사유'  -- LIKE 연산자 사용
            WHERE ud.resolved = FALSE  
            ORDER BY ud.created_at DESC;
        ''')
        unchecked_items = cursor.fetchall()

        # 디버깅을 위한 로깅 추가
        logging.info(f"Found {len(unchecked_items)} unchecked items")
        for item in unchecked_items:
            logging.info(f"Item content: {item[1]}, due days: {item[7]}")

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
                    "due_days": row[7],
                    "deadline": row[8],
                    "is_overdue": row[9]
                } for row in unchecked_items
            ]
        }), 200
    except Exception as e:
        logging.error("Error retrieving unchecked descriptions", exc_info=True)
        return jsonify({"success": False, "message": "미체크 항목 목록을 불러오는 중 오류 발생"}), 500


@training_bp.route('/unchecked_descriptions', methods=['POST'])
def save_unchecked_description():
    """
    미체크 항목 설명과 액션 플랜 저장 API
    ---
    tags:
      - Unchecked Descriptions
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - description
            - action_plan
            - training_course
          properties:
            description:
              type: string
            action_plan:
              type: string
            training_course:
              type: string
    responses:
      201:
        description: 미체크 항목과 액션 플랜이 성공적으로 저장됨
      400:
        description: 필수 데이터 누락
      500:
        description: 서버 오류 발생
    """
    try:
        if not request.is_json:
            return jsonify({"success": False, "message": "Invalid JSON format"}), 400

        data = request.get_json()
        description = data.get("description", "").strip()
        action_plan = data.get("action_plan", "").strip()
        training_course = data.get("training_course", "").strip()

        if not description or not action_plan or not training_course:
            return jsonify({"success": False, "message": "설명, 액션 플랜, 훈련과정명을 모두 입력하세요."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO unchecked_descriptions (content, action_plan, training_course, created_at, resolved)
            VALUES (%s, %s, %s, NOW(), FALSE)
        ''', (description, action_plan, training_course))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "미체크 항목과 액션 플랜이 저장되었습니다!"}), 201

    except Exception as e:
        logging.error("Error saving unchecked description", exc_info=True)
        return jsonify({"success": False, "message": "서버 오류 발생"}), 500


@training_bp.route('/unchecked_comments', methods=['POST'])
def add_unchecked_comment():
    """
    미체크 항목에 댓글 추가 API
    ---
    tags:
      - Unchecked Comments
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - unchecked_id
            - comment
          properties:
            unchecked_id:
              type: integer
            comment:
              type: string
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
        unchecked_id = data.get('unchecked_id')
        comment = data.get('comment')

        if not unchecked_id or not comment:
            return jsonify({"success": False, "message": "미체크 항목 ID와 댓글 내용을 입력하세요."}), 400

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


@training_bp.route('/unchecked_descriptions/resolve', methods=['POST'])
def resolve_unchecked_description():
    """
    미체크 항목 해결 API
    ---
    tags:
      - Unchecked Descriptions
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - unchecked_id
          properties:
            unchecked_id:
              type: integer
    responses:
      200:
        description: 미체크 항목 해결 성공
      400:
        description: 요청 데이터 오류
      500:
        description: 서버 오류 발생
    """
    try:
        data = request.json
        unchecked_id = data.get('unchecked_id')

        if not unchecked_id:
            return jsonify({"success": False, "message": "미체크 항목 ID가 필요합니다."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE unchecked_descriptions SET resolved = TRUE WHERE id = %s", (unchecked_id,))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "미체크 항목이 해결되었습니다."}), 200
    except Exception as e:
        logging.error("Error resolving unchecked description", exc_info=True)
        return jsonify({"success": False, "message": "미체크 항목 해결 실패"}), 500


@training_bp.route('/unchecked_comments', methods=['GET'])
def get_unchecked_comments():
    """
    미체크 항목의 댓글 조회 API
    --- 
    tags:
      - Unchecked Comments
    parameters:
      - name: unchecked_id
        in: query
        type: integer
        required: true
        description: "조회할 미체크 항목 ID"
    responses:
      200:
        description: 미체크 항목의 댓글 목록 반환
      400:
        description: "미체크 항목 ID 누락"
      500:
        description: "댓글 조회 실패"
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