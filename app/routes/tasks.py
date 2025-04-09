from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
from app.models.db import get_db_connection

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/tasks', methods=['GET'])
def get_tasks():
    """
    업무 체크리스트 조회 API
    ---
    tags:
      - Tasks
    summary: 업무 체크리스트 데이터 조회
    parameters:
      - name: task_category
        in: query
        type: string
        required: false
        description: "업무 체크리스트의 카테고리 (예: 개발, 디자인)"
    responses:
      200:
        description: 모든 업무 체크리스트 데이터를 반환함
      500:
        description: 서버 오류로 인해 업무 체크리스트 조회 실패
    """
    try:
        task_category = request.args.get('task_category')  # 선택적 필터링

        conn = get_db_connection()
        cursor = conn.cursor()

        # guide 컬럼 추가
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
                "guide": row[4] if row[4] else "업무 가이드 없음"  # NULL 값 기본 처리
            }
            for row in cursor.fetchall()
        ]

        cursor.close()
        conn.close()

        return jsonify({"success": True, "data": tasks}), 200
    except Exception as e:
        logging.error("Error retrieving tasks", exc_info=True)
        return jsonify({"success": False, "message": "Failed to retrieve tasks"}), 500


@tasks_bp.route('/tasks', methods=['POST'])
def save_tasks():
    """
    업무 체크리스트 저장 API (동일 날짜 데이터는 업데이트)
    ---
    tags:
      - Tasks
    parameters:
      - in: body
        name: body
        description: 저장할 체크리스트 업데이트 데이터
        required: true
        schema:
          type: object
          properties:
            updates:
              type: array
              items:
                type: object
                required:
                  - task_name
                  - is_checked
                properties:
                  task_name:
                    type: string
                  is_checked:
                    type: boolean
            training_course:
              type: string
            username:
              type: string
    responses:
      201:
        description: 업무 체크리스트 저장/업데이트 성공
      400:
        description: 요청 데이터 없음
      500:
        description: 업무 체크리스트 저장 실패
    """
    try:
        data = request.json
        updates = data.get("updates")
        training_course = data.get("training_course")
        username = data.get("username")  # 프론트엔드에서 전달받은 username

        if not updates or not training_course or not username:
            return jsonify({"success": False, "message": "업데이트 데이터, 훈련 과정명, 사용자명이 모두 필요합니다."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # 현재 날짜 가져오기 (시간 제외)
        current_date = datetime.now().date()

        for update in updates:
            task_name = update.get("task_name")
            is_checked = update.get("is_checked", False)

            # task_id 찾기
            cursor.execute("SELECT id FROM task_items WHERE task_name = %s", (task_name,))
            task_item = cursor.fetchone()
            if not task_item:
                continue
            task_id = task_item[0]

            # 동일 날짜의 기존 데이터 확인 (DATE 함수 사용하여 시간 제외)
            cursor.execute("""
                SELECT id 
                FROM task_checklist 
                WHERE task_id = %s 
                AND training_course = %s 
                AND DATE(checked_date)::date = %s::date
            """, (task_id, training_course, current_date))
            
            existing_record = cursor.fetchone()

            if existing_record:
                # 기존 데이터가 있으면 업데이트
                cursor.execute("""
                    UPDATE task_checklist 
                    SET is_checked = %s, checked_date = NOW(), username = %s
                    WHERE id = %s
                """, (is_checked, username, existing_record[0]))
            else:
                # 기존 데이터가 없으면 새로 삽입
                cursor.execute("""
                    INSERT INTO task_checklist (task_id, training_course, is_checked, checked_date, username)
                    VALUES (%s, %s, %s, NOW(), %s)
                """, (task_id, training_course, is_checked, username))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True, 
            "message": "체크리스트가 성공적으로 저장/업데이트되었습니다!"
        }), 201

    except Exception as e:
        logging.error("체크리스트 저장 중 오류 발생", exc_info=True)
        return jsonify({
            "success": False, 
            "message": "체크리스트 저장 실패"
        }), 500


@tasks_bp.route('/tasks/update', methods=['PUT'])
def update_tasks():
    """
    당일 업무 체크리스트 업데이트 API
    ---
    tags:
      - Tasks
    summary: "당일 저장된 체크리스트를 업데이트합니다."
    parameters:
      - in: body
        name: body
        description: 업데이트할 체크리스트 데이터
        required: true
        schema:
          type: object
          properties:
            updates:
              type: array
              items:
                type: object
                required:
                  - task_name
                  - is_checked
                properties:
                  task_name:
                    type: string
                    example: "출석 체크"
                  is_checked:
                    type: boolean
                    example: true
            training_course:
              type: string
              example: "데이터 분석 스쿨 4기"
    responses:
      200:
        description: 체크리스트 업데이트 성공
      404:
        description: 업데이트할 체크리스트가 존재하지 않음
      500:
        description: 업데이트 실패
    """
    try:
        data = request.json
        updates = data.get("updates")
        training_course = data.get("training_course")
        
        # 현재 날짜만 사용 (시간 제외)
        today = datetime.now().date()

        if not updates or not training_course:
            return jsonify({
                "success": False, 
                "message": "업데이트할 데이터와 훈련 과정명이 필요합니다."
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        updated_count = 0
        not_found_items = []

        for update in updates:
            task_name = update.get("task_name")
            is_checked = update.get("is_checked", False)

            # task_id 찾기
            cursor.execute("SELECT id FROM task_items WHERE task_name = %s", (task_name,))
            task_item = cursor.fetchone()
            if not task_item:
                not_found_items.append(task_name)
                continue
                
            task_id = task_item[0]

            # 당일 날짜의 기존 데이터 확인
            cursor.execute("""
                SELECT id 
                FROM task_checklist 
                WHERE task_id = %s 
                AND training_course = %s 
                AND DATE(checked_date)::date = %s::date
            """, (task_id, training_course, today))
            
            existing_record = cursor.fetchone()

            if existing_record:
                # 기존 데이터가 있으면 업데이트
                cursor.execute("""
                    UPDATE task_checklist 
                    SET is_checked = %s, checked_date = NOW()
                    WHERE id = %s
                """, (is_checked, existing_record[0]))
                updated_count += 1
            else:
                # 업데이트할 데이터가 없음
                not_found_items.append(task_name)

        conn.commit()
        cursor.close()
        conn.close()

        if updated_count == 0:
            return jsonify({
                "success": False,
                "message": "당일 저장된 체크리스트가 없어 업데이트할 수 없습니다.",
                "not_found_items": not_found_items
            }), 404

        response = {
            "success": True,
            "message": "체크리스트가 성공적으로 업데이트되었습니다!",
            "updated_count": updated_count
        }
        
        if not_found_items:
            response["warning"] = "일부 항목은 당일 저장된 데이터가 없어 업데이트되지 않았습니다."
            response["not_found_items"] = not_found_items

        return jsonify(response), 200

    except Exception as e:
        logging.error("체크리스트 업데이트 중 오류 발생", exc_info=True)
        return jsonify({
            "success": False,
            "message": "체크리스트 업데이트 실패"
        }), 500


@tasks_bp.route('/irregular_tasks', methods=['GET'])
def get_irregular_tasks():
    """
    비정기 업무 체크리스트 조회 API (가장 최근 상태만 반환)
    ---
    tags:
      - Irregular Tasks
    summary: "비정기 업무 체크리스트의 가장 최근 상태를 조회합니다."
    responses:
      200:
        description: 비정기 업무 체크리스트 조회 성공
      500:
        description: 비정기 업무 조회 실패
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


@tasks_bp.route('/irregular_tasks', methods=['POST'])
def save_irregular_tasks():
    """
    비정기 업무 체크리스트 추가 저장 API
    기존 데이터를 덮어씌우지 않고 새로운 체크 상태를 추가
    ---
    tags:
      - Irregular Tasks
    summary: "비정기 업무 체크리스트 업데이트 데이터를 저장합니다."
    parameters:
      - in: body
        name: body
        description: "저장할 비정기 업무 체크리스트 업데이트 데이터"
        required: true
        schema:
          type: object
          properties:
            updates:
              type: array
              items:
                type: object
                properties:
                  task_name:
                    type: string
                  is_checked:
                    type: boolean
            training_course:
              type: string
    responses:
      201:
        description: 비정기 업무 체크리스트 저장 성공
      500:
        description: 비정기 업무 체크리스트 저장 실패
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