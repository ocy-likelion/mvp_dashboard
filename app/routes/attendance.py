from flask import Blueprint, request, send_file
import logging
from marshmallow import ValidationError

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
@handle_serialization_errors
def get_attendance():
    """
    출퇴근 기록 조회 API (월별 필터링 및 페이지네이션 지원)
    ---
    tags:
      - Attendance
    summary: 출퇴근 기록 조회 및 파일 다운로드 (월별 필터링 및 페이지네이션 지원)
    description: |
      출퇴근 기록을 월별로 필터링하고 페이지네이션을 통해 조회하거나 파일로 다운로드합니다.
      
      ### 사용 예시
      ```javascript
      // 기본 조회 (최신 10개)
      const response = await fetch('/attendance', {
        method: 'GET',
        credentials: 'include'
      });
      
      // 특정 월 조회
      const response = await fetch('/attendance?year=2025&month=1', {
        method: 'GET',
        credentials: 'include'
      });
      
      // 페이지네이션 적용
      const response = await fetch('/attendance?year=2025&month=1&page=2&per_page=5', {
        method: 'GET',
        credentials: 'include'
      });
      
      // 강사별 필터링
      const response = await fetch('/attendance?instructor=1', {
        method: 'GET',
        credentials: 'include'
      });
      
      // Excel 파일로 다운로드
      const response = await fetch('/attendance?format=excel&year=2025&month=1', {
        method: 'GET',
        credentials: 'include'
      });
      
      const result = await response.json();
      console.log(result);
      ```
    parameters:
      - name: page
        in: query
        type: integer
        required: false
        description: "페이지 번호 (기본값: 1)"
        example: 1
      - name: per_page
        in: query
        type: integer
        required: false
        description: "페이지당 항목 수 (기본값: 10, 최대: 100)"
        example: 10
      - name: year
        in: query
        type: integer
        required: false
        description: "조회할 년도"
        example: 2025
      - name: month
        in: query
        type: integer
        required: false
        description: "조회할 월 (1-12)"
        example: 1
      - name: instructor
        in: query
        type: string
        required: false
        description: "강사 ID 필터"
        example: "1"
      - name: training_course
        in: query
        type: string
        required: false
        description: "훈련 과정명 필터"
        example: "데이터 분석 스쿨 4기"
      - name: search
        in: query
        type: string
        required: false
        description: "강사명 또는 훈련과정명 검색"
        example: "홍길동"
      - name: format
        in: query
        type: string
        required: false
        description: "excel 형식으로 다운로드 (기본값 JSON 반환)"
        example: "excel"
      - name: limit
        in: query
        type: integer
        required: false
        description: "조회할 레코드 개수 제한 (페이지네이션 무시)"
        example: 10
    responses:
      200:
        description: 출퇴근 기록 데이터와 페이지네이션 정보 반환 또는 파일 다운로드
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "출퇴근 기록 조회 성공"
            data:
              type: object
              properties:
                items:
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
                pagination:
                  type: object
                  properties:
                    page:
                      type: integer
                      example: 1
                    per_page:
                      type: integer
                      example: 10
                    total_count:
                      type: integer
                      example: 25
                    total_pages:
                      type: integer
                      example: 3
                    has_next:
                      type: boolean
                      example: true
                    has_prev:
                      type: boolean
                      example: false
        examples:
          application/json:
            summary: 출퇴근 기록 조회 성공 응답
            value:
              success: true
              message: "출퇴근 기록 조회 성공"
              data:
                items:
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
                pagination:
                  page: 1
                  per_page: 10
                  total_count: 25
                  total_pages: 3
                  has_next: true
                  has_prev: false
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
        description: 잘못된 파라미터
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "잘못된 월 값입니다."
            details:
              type: object
              example: null
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
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 500
    """
    try:
        format_type = request.args.get("format", "json")  # 기본값 JSON
        
        # 쿼리 파라미터 검증 및 변환
        validated_filters = AttendanceSerializer.deserialize_attendance_list_get(request.args)
        
        # limit 파라미터 처리 (직렬화 오류 방지)
        limit = request.args.get("limit")
        if limit:
            try:
                limit = int(limit)
            except ValueError:
                limit = None
        
        # 페이지네이션을 포함한 출퇴근 기록 조회
        result = AttendanceService.get_attendance_records_paginated(validated_filters, limit)
        
        # 딕셔너리 형태로 변환
        records_data = []
        for record in result["items"]:
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
            response_data = {
                "items": records_data,
                "pagination": result["pagination"]
            }
            return json_response(
                data=response_data,
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
          check_in_time: '09:00',
          check_out_time: '18:00',
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
            - check_in_time
            - check_out_time
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
            check_in_time:
              type: string
              description: 출근 시간 (HH:MM 형식)
              example: "09:00"
            check_out_time:
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
            message:
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
        examples:
          application/json:
            summary: 출퇴근 기록 저장 성공 응답
            value:
              success: true
              message: "출퇴근 기록 저장 성공!"
              data:
                id: 1
                date: "2025-01-15"
                instructor: "1"
                instructor_name: "홍길동"
                training_course: "데이터 분석 스쿨 4기"
                check_in_time: "09:00"
                check_out_time: "18:00"
                daily_log: true
      400:
        description: 데이터 검증 실패 또는 필수 데이터 누락
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "데이터 검증 실패"
            details:
              type: object
              description: 구체적인 검증 오류 정보
              example:
                date: ["날짜는 필수 입력 항목입니다."]
                check_in_time: ["출근 시간은 HH:MM 형식이어야 합니다."]
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
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 500
    """
    try:
        try:
            validated_data = AttendanceSerializer.deserialize_attendance_create(
                request.json
            )
        except ValidationError as e:
            logger.warning(f"Validation error: {e.messages}")
            return error_json_response(
                error="데이터 검증 실패", 
                details=e.messages, 
                status_code=400
            )
        try:
            attendance_data = AttendanceService.create_attendance(validated_data)
        except ValueError as e:
            logger.warning(f"Business logic error: {str(e)}")
            return error_json_response(
                error="출퇴근 기록 저장 실패", 
                details={"business_error": str(e)}, 
                status_code=400
            )

        return json_response(
            data=attendance_data,
            message="출퇴근 기록 저장 성공!",
            status_code=201,
        )
    except Exception as e:
        logger.error("Unexpected error saving attendance", exc_info=True)
        return error_json_response("출퇴근 기록 저장 실패", status_code=500)
