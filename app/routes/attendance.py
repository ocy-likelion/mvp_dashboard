from flask import Blueprint, request, send_file
import logging

from app.serializers import (
    AttendanceSerializer,
    json_response,
    error_json_response,
    handle_serialization_errors,
)
from app.services import AttendanceService

attendance_bp = Blueprint("attendance", __name__)
logger = logging.getLogger(__name__)


@attendance_bp.route("/attendance", methods=["GET"])
def get_attendance():
    """
    출퇴근 기록 조회 API
    ---
    tags:
      - Attendance
    summary: 출퇴근 기록 조회 및 파일 다운로드
    description: |
      출퇴근 기록을 조회하거나 파일로 다운로드합니다.
      
      ### 사용 예시
      ```javascript
      // JSON 형태로 조회
      const response = await fetch('/attendance', {
        method: 'GET',
        credentials: 'include'
      });
      
      // Excel 파일로 다운로드
      const response = await fetch('/attendance?format=excel', {
        method: 'GET',
        credentials: 'include'
      });
      
      // 특정 개수만 조회
      const response = await fetch('/attendance?limit=10', {
        method: 'GET',
        credentials: 'include'
      });
      
      const result = await response.json();
      console.log(result);
      ```
    parameters:
      - name: format
        in: query
        type: string
        required: false
        description: "csv 또는 excel 형식으로 다운로드 (기본값 JSON 반환)"
        example: "excel"
      - name: limit
        in: query
        type: integer
        required: false
        description: "조회할 레코드 개수 제한"
        example: 10
    responses:
      200:
        description: 출퇴근 기록 데이터 반환 또는 파일 다운로드
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            error:
              type: string
              example: "출퇴근 기록 조회 성공"
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  date:
                    type: string
                    format: date
                    example: "2025-01-15"
                  instructor:
                    type: string
                    example: "1"
                  instructor_name:
                    type: string
                    example: "홍길동"
                  training_course:
                    type: string
                    example: "데이터 분석 스쿨 4기"
                  check_in_time:
                    type: string
                    example: "09:00"
                  check_out_time:
                    type: string
                    example: "18:00"
                  daily_log:
                    type: boolean
                    example: true
            status_code:
              type: integer
              example: 200
        examples:
          application/json:
            summary: 출퇴근 기록 조회 성공 응답
            value:
              success: true
              error: "출퇴근 기록 조회 성공"
              data:
                - id: 1
                  date: "2025-01-15"
                  instructor: "1"
                  instructor_name: "홍길동"
                  training_course: "데이터 분석 스쿨 4기"
                  check_in_time: "09:00"
                  check_out_time: "18:00"
                  daily_log: true
                - id: 2
                  date: "2025-01-14"
                  instructor: "2"
                  instructor_name: "김철수"
                  training_course: "데이터 분석 스쿨 4기"
                  check_in_time: "08:30"
                  check_out_time: "17:30"
                  daily_log: false
              status_code: 200
        headers:
          Content-Disposition:
            description: 파일 다운로드 시 헤더
            schema:
              type: string
              example: "attachment; filename=출퇴근_기록.xlsx"
          Content-Type:
            description: 파일 타입
            schema:
              type: string
              example: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      400:
        description: 잘못된 포맷 요청
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "잘못된 포맷 요청"
            status_code:
              type: integer
              example: 400
      500:
        description: 데이터 조회 실패
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "출퇴근 기록 조회 실패"
            status_code:
              type: integer
              example: 500
    """
    try:
        format_type = request.args.get("format", "json")  # 기본값 JSON
        # 간단한 파라미터 처리 (직렬화 오류 방지)
        limit = request.args.get("limit")
        if limit:
            try:
                limit = int(limit)
            except ValueError:
                limit = None
        
        attendance_records = AttendanceService.get_attendance_records(limit)
        
        # 딕셔너리 형태로 변환
        records_data = []
        for record in attendance_records:
            record_dict = {
                "id": record.id,
                "date": record.date.strftime("%Y-%m-%d"),
                "instructor": record.instructor,
                "instructor_name": record.instructor_name,
                "training_course": record.training_course,
                "check_in_time": record.check_in_time.strftime("%H:%M") if record.check_in_time else None,
                "check_out_time": record.check_out_time.strftime("%H:%M") if record.check_out_time else None,
                "daily_log": record.daily_log,
            }
            records_data.append(record_dict)

        # JSON 응답 (기본값)
        if format_type == "json":
            return json_response(
                data=records_data,
                message="출퇴근 기록 조회 성공",
                status_code=200,
            )

        # Excel 파일 다운로드
        elif format_type == "excel":
            # Service를 사용한 Excel 파일 생성
            excel_file = AttendanceService.generate_excel_file(records_data)
            return send_file(
                excel_file,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                as_attachment=True,
                download_name="출퇴근_기록.xlsx",
            )

        else:
            return error_json_response("잘못된 포맷 요청", status_code=400)

    except Exception as e:
        logger.error("출퇴근 기록 조회 오류", exc_info=True)
        return error_json_response("출퇴근 기록 조회 실패", status_code=500)


@attendance_bp.route("/attendance", methods=["POST"])
@handle_serialization_errors
def save_attendance():
    """
    출퇴근 기록 저장 API
    ---
    tags:
      - Attendance
    summary: 새로운 출퇴근 기록 저장
    description: |
      새로운 출퇴근 기록을 저장합니다.
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/attendance', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          date: '2025-01-15',
          instructor: '1',
          instructor_name: '홍길동',
          training_course: '데이터 분석 스쿨 4기',
          check_in: '09:00',
          check_out: '18:00',
          daily_log: true
        })
      });
      
      const result = await response.json();
      console.log(result);
      ```
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
              description: 출퇴근 날짜
              example: "2025-01-15"
            instructor:
              type: string
              description: 강사 ID
              example: "1"
            instructor_name:
              type: string
              description: 강사명
              example: "홍길동"
            training_course:
              type: string
              description: 훈련 과정명
              example: "데이터 분석 스쿨 4기"
            check_in:
              type: string
              description: 출근 시간 (HH:MM 형식)
              example: "09:00"
            check_out:
              type: string
              description: 퇴근 시간 (HH:MM 형식)
              example: "18:00"
            daily_log:
              type: boolean
              description: 일일 로그 작성 여부
              example: true
    responses:
      201:
        description: 출퇴근 기록 저장 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            error:
              type: string
              example: "출퇴근 기록 저장 성공!"
            data:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                date:
                  type: string
                  format: date
                  example: "2025-01-15"
                instructor:
                  type: string
                  example: "1"
                instructor_name:
                  type: string
                  example: "홍길동"
                training_course:
                  type: string
                  example: "데이터 분석 스쿨 4기"
                check_in_time:
                  type: string
                  example: "09:00"
                check_out_time:
                  type: string
                  example: "18:00"
                daily_log:
                  type: boolean
                  example: true
            status_code:
              type: integer
              example: 201
        examples:
          application/json:
            summary: 출퇴근 기록 저장 성공 응답
            value:
              success: true
              error: "출퇴근 기록 저장 성공!"
              data:
                id: 1
                date: "2025-01-15"
                instructor: "1"
                instructor_name: "홍길동"
                training_course: "데이터 분석 스쿨 4기"
                check_in_time: "09:00"
                check_out_time: "18:00"
                daily_log: true
              status_code: 201
      400:
        description: 필수 데이터 누락
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "날짜, 강사 정보, 훈련 과정, 출퇴근 시간은 필수 입력 항목입니다."
            status_code:
              type: integer
              example: 400
      500:
        description: 출퇴근 기록 저장 실패
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "출퇴근 기록 저장 실패"
            status_code:
              type: integer
              example: 500
    """
    try:
        validated_data = AttendanceSerializer.deserialize_attendance_create(
            request.json
        )
        attendance_data = AttendanceService.create_attendance(validated_data)

        return json_response(
            data=attendance_data,
            message="출퇴근 기록 저장 성공!",
            status_code=201,
        )
    except Exception as e:
        logger.error("Error saving attendance", exc_info=True)
        return error_json_response("출퇴근 기록 저장 실패", status_code=500)
