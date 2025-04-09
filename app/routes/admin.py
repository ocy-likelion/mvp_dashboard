from flask import Blueprint, request, jsonify
import logging
from app.models.db import get_db_connection

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/task_status', methods=['GET'])
def get_task_status():
    """
    훈련 과정별 업무 체크리스트의 체크율을 조회하는 API
    ---
    tags:
      - Admin
    summary: "훈련 과정별 업무 체크 상태 및 부서 정보 조회"
    responses:
      200:
        description: 훈련 과정별 체크율 데이터를 반환
      500:
        description: 체크 상태 조회 실패
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # training_info 테이블을 조인하여 dept 정보 포함
        cursor.execute('''
            SELECT tc.training_course, ti.dept, 
                   COUNT(*) AS total_tasks, 
                   SUM(CASE WHEN tc.is_checked THEN 1 ELSE 0 END) AS checked_tasks
            FROM task_checklist tc
            JOIN training_info ti ON tc.training_course = ti.training_course
            WHERE DATE(tc.checked_date) = CURRENT_DATE  -- 당일 체크된 데이터만 필터링
            GROUP BY tc.training_course, ti.dept
        ''')
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        task_status = []
        for row in results:
            training_course = row[0]
            dept = row[1]
            total_tasks = row[2]
            checked_tasks = row[3] if row[3] else 0
            check_rate = round((checked_tasks / total_tasks) * 100, 2) if total_tasks > 0 else 0

            task_status.append({
                "training_course": training_course,
                "dept": dept,
                "check_rate": f"{check_rate}%"
            })

        return jsonify({"success": True, "data": task_status}), 200
    except Exception as e:
        logging.error("Error retrieving task status", exc_info=True)
        return jsonify({"success": False, "message": "Failed to retrieve task status"}), 500


@admin_bp.route('/admin/task_status_overall', methods=['GET'])
def get_overall_task_status():
    """
    훈련 과정별 전체 체크율을 조회하는 API
    ---
    tags:
      - Admin
    responses:
      200:
        description: 훈련 과정별 전체 체크율 데이터 반환
      500:
        description: 체크율 조회 실패
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT tc.training_course, ti.dept, 
                   COUNT(*) AS total_tasks, 
                   SUM(CASE WHEN tc.is_checked THEN 1 ELSE 0 END) AS checked_tasks
            FROM task_checklist tc
            JOIN training_info ti ON tc.training_course = ti.training_course
            GROUP BY tc.training_course, ti.dept
        ''')
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        task_status = []
        for row in results:
            training_course, dept, total_tasks, checked_tasks = row
            check_rate = round((checked_tasks / total_tasks) * 100, 2) if total_tasks > 0 else 0

            task_status.append({
                "training_course": training_course,
                "dept": dept,
                "check_rate": f"{check_rate}%"
            })

        return jsonify({"success": True, "data": task_status}), 200
    except Exception as e:
        logging.error("Error retrieving overall task status", exc_info=True)
        return jsonify({"success": False, "message": "Failed to retrieve overall task status"}), 500


@admin_bp.route('/admin/task_status_combined', methods=['GET'])
def get_combined_task_status():
    """
    훈련 과정별 업무 체크리스트의 체크율(당일, 전날, 전체)을 조회하는 API
    --- 
    tags:
      - Admin
    summary: "훈련 과정별 업무 체크율 조회"
    description: "각 훈련 과정별로 담당자, 당일 체크율, 전날 체크율, 전체 체크율을 조회합니다."
    responses:
      200:
        description: 훈련 과정별 체크율 데이터 반환
      500:
        description: 체크 상태 조회 실패
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                tc.training_course, 
                ti.dept,
                ti.manager_name,
                ti.end_date,  -- end_date 컬럼 추가
                COUNT(*) AS total_tasks,
                SUM(CASE WHEN tc.is_checked THEN 1 ELSE 0 END) AS checked_tasks,
                -- 당일 체크 데이터
                SUM(CASE WHEN tc.is_checked AND DATE(tc.checked_date) = CURRENT_DATE THEN 1 ELSE 0 END) AS daily_checked_tasks,
                COUNT(CASE WHEN DATE(tc.checked_date) = CURRENT_DATE THEN 1 ELSE NULL END) AS daily_total_tasks,
                -- 전날 체크 데이터
                SUM(CASE WHEN tc.is_checked AND DATE(tc.checked_date) = CURRENT_DATE - INTERVAL '1 day' THEN 1 ELSE 0 END) AS yesterday_checked_tasks,
                COUNT(CASE WHEN DATE(tc.checked_date) = CURRENT_DATE - INTERVAL '1 day' THEN 1 ELSE NULL END) AS yesterday_total_tasks
            FROM task_checklist tc
            JOIN training_info ti ON tc.training_course = ti.training_course
            WHERE ti.end_date >= CURRENT_DATE - INTERVAL '7 days'  -- 종료된 지 1주일 이내의 과정만 포함
            GROUP BY tc.training_course, ti.dept, ti.manager_name, ti.end_date  -- end_date 추가
            ORDER BY ti.end_date DESC
        ''')

        results = cursor.fetchall()
        cursor.close()
        conn.close()

        task_status = []
        for row in results:
            training_course = row[0]
            dept = row[1]
            manager_name = row[2] if row[2] else "담당자 없음"
            total_tasks = row[4]  # 인덱스 수정
            checked_tasks = row[5] if row[5] else 0  # 인덱스 수정
            daily_checked_tasks = row[6] if row[6] else 0  # 인덱스 수정
            daily_total_tasks = row[7] if row[7] else 0  # 인덱스 수정
            yesterday_checked_tasks = row[8] if row[8] else 0  # 인덱스 수정
            yesterday_total_tasks = row[9] if row[9] else 0  # 인덱스 수정

            # 전체 체크율 계산
            overall_check_rate = round((checked_tasks / total_tasks) * 100, 2) if total_tasks > 0 else 0
            # 당일 체크율 계산
            daily_check_rate = round((daily_checked_tasks / daily_total_tasks) * 100, 2) if daily_total_tasks > 0 else 0
            # 전날 체크율 계산
            yesterday_check_rate = round((yesterday_checked_tasks / yesterday_total_tasks) * 100, 2) if yesterday_total_tasks > 0 else 0

            task_status.append({
                "training_course": training_course,
                "dept": dept,
                "manager_name": manager_name,
                "daily_check_rate": f"{daily_check_rate}%",
                "yesterday_check_rate": f"{yesterday_check_rate}%",
                "overall_check_rate": f"{overall_check_rate}%"
            })

        return jsonify({"success": True, "data": task_status}), 200
    except Exception as e:
        logging.error("Error retrieving combined task status", exc_info=True)
        return jsonify({"success": False, "message": "체크율 정보를 불러오는데 실패했습니다."}), 500