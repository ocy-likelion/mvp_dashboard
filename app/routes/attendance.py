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
        format_type = request.args.get("format", "json")  # 기본값 JSON
        validated_data = AttendanceSerializer.deserialize_attendance_get(request.args)
        attendance_records = AttendanceService.get_attendance_records(validated_data)
        serialized_records = AttendanceSerializer.serialize_attendances(
            attendance_records
        )

        # JSON 응답 (기본값)
        if format_type == "json":
            return json_response(
                data=serialized_records,
                message="출퇴근 기록 조회 성공",
                status_code=200,
            )

        # Excel 파일 다운로드
        elif format_type == "excel":
            # Service를 사용한 Excel 파일 생성
            excel_file = AttendanceService.generate_excel_file(serialized_records)
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
        validated_data = AttendanceSerializer.deserialize_attendance_create(
            request.json
        )
        attendance = AttendanceService.create_attendance(validated_data)
        serialized_attendance = AttendanceSerializer.serialize_attendance(attendance)

        return json_response(
            data=serialized_attendance,
            message="출퇴근 기록 저장 성공!",
            status_code=201,
        )
    except Exception as e:
        logger.error("Error saving attendance", exc_info=True)
        return error_json_response("출퇴근 기록 저장 실패", status_code=500)
