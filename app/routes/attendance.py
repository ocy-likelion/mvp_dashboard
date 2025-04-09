from flask import Blueprint, request, jsonify, send_file
import io
import pandas as pd
import logging
from app.models.db import get_db_connection

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/attendance', methods=['GET'])
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

        # JSON 응답 (기본값)
        if format_type == 'json':
            return jsonify({"success": True, "data": df.to_dict(orient='records')}), 200

        # Excel 파일 다운로드
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

@attendance_bp.route('/attendance', methods=['POST'])
def save_attendance():
    """
    출퇴근 기록 저장 API
    ---
    tags:
      - Attendance
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
            instructor_name:
              type: string
              example: "홍길동"
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
        instructor_name = data.get('instructor_name')
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