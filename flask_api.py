import io
import pandas as pd
from flask import Flask, Response, request, jsonify, render_template, redirect, send_file, url_for, session, flash
from flask_cors import CORS  # CORS 추가
from flasgger import Swagger, swag_from
from dotenv import load_dotenv
import os, psycopg2
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.ERROR)

app = Flask(__name__, template_folder='templates')
app.secret_key = 'your-secret-key'  # 실제 운영 환경에서는 안전한 난수를 사용하세요.
CORS(app, supports_credentials=True)  # ✅ CORS 설정 강화 (세션 쿠키 허용)

app.config['SWAGGER'] = {
    'title': "업무 관리 대시보드 API",
    'uiversion': 3,  # 최신 Swagger UI 사용
    'specs_route': "/apidocs"  # ✅ 끝의 슬래시(/) 제거
}
swagger = Swagger(app)  # Flasgger 초기화

# ✅ .env 파일에서 환경 변수 로드
load_dotenv()

# PostgreSQL 데이터베이스 연결 함수
def get_db_connection():
    DATABASE_URL = os.getenv("DATABASE_URL")  # ✅ 환경 변수 읽기
    
    # 환경 변수가 없으면 강제 설정 (백업용, 하지만 로컬에서는 .env가 있으므로 필요 없음)
    if not DATABASE_URL:
        DATABASE_URL = "postgresql://cysss:QJxyP6VuLMAZykzMyeRtO3QJUGMf0aWA@dpg-cuim9pogph6c73acoj0g-a/mvp_dashboard"
    
    conn = psycopg2.connect(DATABASE_URL)
    return conn
    

# ------------------- API 엔드포인트 문서화 시작 -------------------

# healthcheck 라우트 -> DB 확인하기 위함
@app.route('/healthcheck', methods=['GET'])
@swag_from({
    'tags': ['System'],
    'summary': '서버 상태 확인',
    'responses': {
        200: {
            'description': '서버가 정상적으로 작동함',
            'schema': {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string'},
                    'message': {'type': 'string'}
                }
            }
        }
    }
})
def healthcheck():
    return jsonify({"status": "ok", "message": "Service is running!"}), 200


# ✅ 로그인 API
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"success": False, "message": "ID와 비밀번호를 입력하세요."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user or user[1] != password:
            return jsonify({"success": False, "message": "잘못된 ID 또는 비밀번호입니다."}), 401

        session['user'] = {"id": user[0], "username": username}
        return jsonify({"success": True, "message": "로그인 성공!"}), 200

    except Exception as e:
        logging.error("로그인 오류", exc_info=True)
        return jsonify({"success": False, "message": "서버 오류 발생"}), 500


# ✅ 로그아웃 API
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({"success": True, "message": "로그아웃 완료!"}), 200


# ✅ 로그인 상태 확인 API
@app.route('/me', methods=['GET'])
def get_current_user():
    if 'user' not in session:
        return jsonify({"success": False, "message": "로그인이 필요합니다."}), 401
    return jsonify({"success": True, "user": session['user']}), 200


# front_for_pro 페이지
@app.route('/front_for_pro', methods=['GET'])
def front_for_pro():
    """
    프론트엔드 개발자용 대시보드 API
    ---
    tags:
      - Views
    summary: 프론트엔드 개발자를 위한 대시보드 페이지 반환
    description: 
      사용자가 로그인한 경우 대시보드 페이지 (front_for_pro.html)을 반환합니다.
      로그인하지 않은 경우 로그인 페이지로 이동됩니다.
    responses:
      200:
        description: 대시보드 HTML 페이지 반환
      302:
        description: 로그인되지 않은 경우 로그인 페이지로 리다이렉트
    """
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('front_for_pro.html')


# admin 페이지
@app.route('/admin', methods=['GET'])
def admin():
    """
    관리자 대시보드 API
    ---
    tags:
      - Views
    summary: 관리자 대시보드 페이지 반환
    description: 
      사용자가 로그인한 경우 관리자 대시보드 (admin.html)을 반환합니다.  
      로그인하지 않은 경우 로그인 페이지로 이동됩니다.
    responses:
      200:
        description: 관리자 대시보드 HTML 페이지 반환
      302:
        description: 로그인되지 않은 경우 로그인 페이지로 리다이렉트
    """
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('admin.html')


@app.route('/notices', methods=['GET'])
def get_notices():
    """
    공지사항 및 전달사항 조회 API
    ---
    tags:
      - Notices
    responses:
      200:
        description: 공지사항 및 전달사항 데이터를 포함한 응답
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: object
              properties:
                notices:
                  type: array
                  description: 모든 공지사항 데이터
                remarks:
                  type: array
                  description: "전달사항 타입인 공지 데이터"
      500:
        description: 공지사항을 불러오는 데 실패함
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # 공지사항과 전달사항을 모두 불러옴
        cursor.execute('SELECT * FROM notices ORDER BY date DESC')
        notices = cursor.fetchall()
        cursor.close()
        conn.close()
        # '전달사항'만 필터링하여 별도로 제공 (notice[1]가 타입으로 가정)
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


@app.route('/notices', methods=['POST'])
def add_notice():
    """
    공지사항 추가 API
    ---
    tags:
      - Notices
    summary: 새로운 공지사항을 추가합니다.
    description: 
      사용자가 새로운 공지사항을 등록할 수 있습니다.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - title
            - content
          properties:
            title:
              type: string
              example: "시스템 점검 안내"
            content:
              type: string
              example: "금일 오후 6시부터 8시까지 시스템 점검이 진행됩니다."
    responses:
      201:
        description: 공지사항 추가 성공
      400:
        description: 필수 데이터 누락
      500:
        description: 서버 오류 발생
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


# 과정명 선택할 수 있는 드롭다운 설정
@app.route('/training_courses', methods=['GET'])
def get_training_courses():
    """
    training_info 테이블에서 training_course 목록을 가져오는 API
    ---
    tags:
      - Training Info
    responses:
      200:
        description: 훈련과정 목록 반환
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                type: string
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
            "data": [course[0] for course in courses]  # 리스트 형태로 반환
        }), 200
    except Exception as e:
        logging.error("Error fetching training courses", exc_info=True)
        return jsonify({"success": False, "message": "Failed to fetch training courses"}), 500


@app.route('/attendance', methods=['GET'])
def get_attendance():
    """
    출퇴근 기록 파일 다운로드 API
    ---
    tags:
      - Attendance
    parameters:
      - name: format
        in: query
        type: string
        required: false
        description: "csv 또는 excel 형식으로 다운로드 (기본값 JSON 반환)"
    responses:
      200:
        description: 출퇴근 기록 데이터 반환 또는 파일 다운로드
      500:
        description: 데이터 조회 실패
    """
    try:
        format_type = request.args.get('format', 'json')  # 기본값 JSON
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, date, instructor, training_course, check_in, check_out, daily_log FROM attendance ORDER BY date DESC')
        attendance_records = cursor.fetchall()
        cursor.close()
        conn.close()

        columns = ['ID', '날짜', '강사', '훈련과정', '출근 시간', '퇴근 시간', '일지 작성 완료']
        df = pd.DataFrame(attendance_records, columns=columns)

        # ✅ JSON 응답 (기본값)
        if format_type == 'json':
            return jsonify({"success": True, "data": df.to_dict(orient='records')}), 200

        # ✅ Excel 파일 다운로드
        elif format_type == 'excel':
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name="출퇴근 기록")
            output.seek(0)
            return send_file(
                output,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                as_attachment=True,
                download_name="출퇴근_기록.xlsx"
            )

        else:
            return jsonify({"success": False, "message": "잘못된 포맷 요청"}), 400

    except Exception as e:
        logging.error("출퇴근 기록 조회 오류", exc_info=True)
        return jsonify({"success": False, "message": "출퇴근 기록 조회 실패"}), 500


# 출퇴근 기록 저장
@app.route('/attendance', methods=['POST'])
def save_attendance():
    """
    출퇴근 기록 저장 API
    ---
    tags:
      - Attendance
    summary: 출퇴근 기록을 저장합니다.
    description: 
      - 강사명이 포함된 출퇴근 기록을 attendance 테이블에 저장합니다.
      - 주강사와 보조강사의 출퇴근 기록을 분리하여 저장합니다.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - date
            - instructor
            - instructor_name
            - training_course
            - check_in
            - check_out
          properties:
            date:
              type: string
              format: date
              example: "2025-02-12"
            instructor:
              type: string
              example: "1"
              description: "1: 주강사, 2: 보조강사"
            instructor_name:
              type: string
              example: "홍길동"
              description: "강사 이름"
            training_course:
              type: string
              example: "데이터 분석 스쿨"
            check_in:
              type: string
              example: "09:00"
            check_out:
              type: string
              example: "18:00"
            daily_log:
              type: boolean
              example: true
              description: "일지 작성 여부"
    responses:
      201:
        description: 출퇴근 기록 저장 성공
      400:
        description: 필수 데이터 누락
      500:
        description: 출퇴근 기록 저장 실패
    """
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400

        date = data.get('date')
        instructor = data.get('instructor')
        instructor_name = data.get('instructor_name')  # ✅ 강사명 추가
        training_course = data.get('training_course')
        check_in = data.get('check_in')
        check_out = data.get('check_out')
        daily_log = data.get('daily_log', False)

        if not date or not instructor or not instructor_name or not training_course or not check_in or not check_out:
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO attendance (date, instructor, instructor_name, training_course, check_in, check_out, daily_log)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (date, instructor, instructor_name, training_course, check_in, check_out, daily_log))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Attendance saved!"}), 201
    except Exception as e:
        logging.error("Error saving attendance", exc_info=True)
        return jsonify({"success": False, "message": "Failed to save attendance"}), 500


@app.route('/tasks', methods=['GET'])
def get_tasks():
    """
    업무 체크리스트 조회 API
    ---
    tags:
      - Tasks
    summary: 업무 체크리스트 데이터 조회
    description: 
      모든 업무 체크리스트 데이터를 조회합니다.  
      task_category를 기준으로 필터링할 수 있습니다.
    parameters:
      - name: task_category
        in: query
        type: string
        required: false
        description: "업무 체크리스트의 카테고리 (예: 개발, 디자인)"
    responses:
      200:
        description: 모든 업무 체크리스트 데이터를 반환함
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  task_name:
                    type: string
                  task_period:
                    type: string
                  task_category:
                    type: string
                  guide:
                    type: string
      400:
        description: "잘못된 요청 (예: 유효하지 않은 task_category 값)"
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
      500:
        description: 서버 오류로 인해 업무 체크리스트 조회 실패
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
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


@app.route('/tasks', methods=['POST'])
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

        if not updates or not training_course:
            return jsonify({"success": False, "message": "데이터가 제공되지 않았습니다."}), 400

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
                    SET is_checked = %s, checked_date = NOW()
                    WHERE id = %s
                """, (is_checked, existing_record[0]))
            else:
                # 기존 데이터가 없으면 새로 삽입
                cursor.execute("""
                    INSERT INTO task_checklist (task_id, training_course, is_checked, checked_date)
                    VALUES (%s, %s, %s, NOW())
                """, (task_id, training_course, is_checked))

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


@app.route('/tasks/update', methods=['PUT'])
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


@app.route('/remarks', methods=['POST'])
def save_remarks():
    """
    전달사항 저장 API
    ---
    tags:
      - Remarks
    parameters:
      - in: body
        name: body
        description: 저장할 전달사항 데이터
        required: true
        schema:
          type: object
          required:
            - remarks
          properties:
            remarks:
              type: string
              example: "전달사항 내용 예시"
    responses:
      201:
        description: 전달사항 저장 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
      400:
        description: 전달사항 데이터 누락
      500:
        description: 전달사항 저장 실패
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

@app.route('/issues', methods=['POST'])
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



@app.route('/issues', methods=['GET'])
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
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  content:
                    type: string
                  date:
                    type: string
                  training_course:
                    type: string
                  created_at:
                    type: string
                  resolved:
                    type: boolean
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


# 이슈에 대한 댓글 달기
@app.route('/issues/comments', methods=['POST'])
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
          properties:
            issue_id:
              type: integer
              example: 1
            comment:
              type: string
              example: "이슈에 대한 답변입니다."
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

# 이슈에 대한 댓글 조회
@app.route('/issues/comments', methods=['GET'])
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
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  comment:
                    type: string
                  created_at:
                    type: string
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
            "SELECT id, comment, created_at FROM issue_comments WHERE issue_id = %s ORDER BY created_at ASC",
            (issue_id,)
        )
        comments = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": [{"id": row[0], "comment": row[1], "created_at": row[2]} for row in comments]
        }), 200
    except Exception as e:
        logging.error("Error retrieving issue comments", exc_info=True)
        return jsonify({"success": False, "message": "댓글 조회 실패"}), 500

# 해결된 이슈 클릭
@app.route('/issues/resolve', methods=['POST'])
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
@app.route('/issues/download', methods=['GET'])
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


@app.route('/irregular_tasks', methods=['GET'])
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
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  task_name:
                    type: string
                  is_checked:
                    type: boolean
                  checked_date:
                    type: string
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



@app.route('/irregular_tasks', methods=['POST'])
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



@app.route('/training_info', methods=['POST'])
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


@app.route('/training_info', methods=['GET'])
def get_training_info():
    """
    훈련 과정 목록 조회 API
    ---
    tags:
      - Training Info
    responses:
      200:
        description: 저장된 훈련 과정 목록 반환
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                type: object
                properties:
                  training_course:
                    type: string
                  start_date:
                    type: string
                  end_date:
                    type: string
                  dept:
                    type: string
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



# ✅ 미체크 항목의 설명 불러오기 (부서명 포함)
@app.route('/unchecked_descriptions', methods=['GET'])
def get_unchecked_descriptions():
    """
    미체크 항목 설명 및 액션 플랜 조회 API (부서명 포함)

    ---
    tags:
      - Unchecked Descriptions
    summary: 미체크 항목 설명 및 액션 플랜 조회
    description:
      데이터베이스에서 해결되지 않은 미체크 항목 목록을 조회하여 반환합니다.
      반환된 데이터에는 각 항목의 설명, 액션 플랜 및 과정명에 해당하는 부서명이 포함됩니다.
    responses:
      200:
        description: 미체크 항목 목록 조회 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  content:
                    type: string
                    example: "출석 체크 시스템 오류로 인해 확인 불가"
                  action_plan:
                    type: string
                    example: "출석 체크 기능 복구 요청 및 대체 방안 검토"
                  training_course:
                    type: string
                    example: "데이터 분석 스쿨 100기"
                  dept:
                    type: string
                    example: "TechSol"
                  created_at:
                    type: string
                    example: "2025-02-12 10:30:00"
                  resolved:
                    type: boolean
                    example: false
      500:
        description: 미체크 항목 목록 조회 실패
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # ✅ training_info 테이블을 조인하여 dept 정보 포함
        cursor.execute('''
            SELECT ud.id, ud.content, ud.action_plan, ud.training_course, ti.dept, ud.created_at, ud.resolved
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
                    "content": row[1],  # 항목 설명
                    "action_plan": row[2],  # 액션 플랜
                    "training_course": row[3],
                    "dept": row[4],  # ✅ 부서명 추가
                    "created_at": row[5],
                    "resolved": row[6]
                } for row in unchecked_items
            ]
        }), 200
    except Exception as e:
        logging.error("Error retrieving unchecked descriptions", exc_info=True)
        return jsonify({"success": False, "message": "미체크 항목 목록을 불러오는 중 오류 발생"}), 500


# ✅ 미체크 항목 저장
@app.route('/unchecked_descriptions', methods=['POST'])
def save_unchecked_description():
    """
    미체크 항목 설명과 액션 플랜 저장 API

    ---
    tags:
      - Unchecked Descriptions
    summary: 미체크 항목 설명 및 액션 플랜 저장
    description: 
      사용자가 미체크 항목(설명)과 해당 액션 플랜을 입력하여 데이터베이스에 저장합니다.
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
              example: "출석 체크 시스템 오류로 인해 확인 불가"
            action_plan:
              type: string
              example: "출석 체크 기능 복구 요청 및 대체 방안 검토"
            training_course:
              type: string
              example: "데이터 분석 스쿨 100기"
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


# ✅ 미체크 항목 댓글 저장
@app.route('/unchecked_comments', methods=['POST'])
def add_unchecked_comment():
    """
    미체크 항목에 댓글 추가 API
    ---
    tags:
      - Unchecked Comments
    summary: 미체크 항목에 대한 댓글을 저장합니다.
    description: 사용자가 특정 미체크 항목에 대해 댓글을 추가할 수 있습니다.
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
              example: 1
            comment:
              type: string
              example: "확인 후 조치 예정입니다."
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


# ✅ 미체크 항목 댓글 해결
@app.route('/unchecked_descriptions/resolve', methods=['POST'])
def resolve_unchecked_description():
    """
    미체크 항목 해결 API
    ---
    tags:
      - Unchecked Descriptions
    summary: 특정 미체크 항목을 해결 상태로 변경합니다.
    description: 사용자가 특정 미체크 항목을 해결했음을 표시합니다.
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
              example: 1
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

# 미체크 항목 댓글 불러오기
@app.route('/unchecked_comments', methods=['GET'])
def get_unchecked_comments():
    """
    미체크 항목의 댓글 조회 API
    --- 
    tags:
      - Unchecked Comments
    summary: "특정 미체크 항목의 댓글 목록을 조회합니다."
    parameters:
      - name: unchecked_id
        in: query
        type: integer
        required: true
        description: "조회할 미체크 항목 ID"
    responses:
      200:
        description: 미체크 항목의 댓글 목록 반환
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  comment:
                    type: string
                  created_at:
                    type: string
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


# 당일 체크율 계산
@app.route('/admin/task_status', methods=['GET'])
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
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                type: object
                properties:
                  training_course:
                    type: string
                  dept:
                    type: string
                  check_rate:
                    type: string
      500:
        description: 체크 상태 조회 실패
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # ✅ training_info 테이블을 조인하여 dept 정보 포함
        cursor.execute('''
            SELECT tc.training_course, ti.dept, 
                   COUNT(*) AS total_tasks, 
                   SUM(CASE WHEN tc.is_checked THEN 1 ELSE 0 END) AS checked_tasks
            FROM task_checklist tc
            JOIN training_info ti ON tc.training_course = ti.training_course
            WHERE DATE(tc.checked_date) = CURRENT_DATE  -- 🔥 당일 체크된 데이터만 필터링
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


# 전체 체크율 계산
@app.route('/admin/task_status_overall', methods=['GET'])
def get_overall_task_status():
    """
    훈련 과정별 전체 체크율을 조회하는 API
    ---
    responses:
      200:
        description: 훈련 과정별 전체 체크율 데이터 반환
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


@app.route('/admin/task_status_combined', methods=['GET'])
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
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                type: object
                properties:
                  training_course:
                    type: string
                  dept:
                    type: string
                  manager_name:
                    type: string
                  daily_check_rate:
                    type: string
                  yesterday_check_rate:
                    type: string
                  overall_check_rate:
                    type: string
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
            GROUP BY tc.training_course, ti.dept, ti.manager_name
        ''')

        results = cursor.fetchall()
        cursor.close()
        conn.close()

        task_status = []
        for row in results:
            training_course = row[0]
            dept = row[1]
            manager_name = row[2] if row[2] else "담당자 없음"
            total_tasks = row[3]
            checked_tasks = row[4] if row[4] else 0
            daily_checked_tasks = row[5] if row[5] else 0
            daily_total_tasks = row[6] if row[6] else 0
            yesterday_checked_tasks = row[7] if row[7] else 0
            yesterday_total_tasks = row[8] if row[8] else 0

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
        return jsonify({"success": False, "message": "Failed to retrieve task status"}), 500



# ------------------- API 엔드포인트 문서화 끝 -------------------
 
@app.route('/', methods=['GET'])
def index():
    """
    서버 상태 확인용 루트 경로
    ---
    tags:
      - System
    responses:
      200:
        description: 서버가 정상적으로 실행 중임
    """
    return jsonify({
        "status": "ok",
        "message": "API 서버가 정상적으로 실행 중입니다.",
        "version": "1.0.0"
    }), 200

if __name__ == '__main__':
    port = int(os.getenv("PORT", 10000))  # 기본값을 10000으로 설정
    app.run(host="0.0.0.0", port=port)