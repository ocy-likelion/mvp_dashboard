from flask import Blueprint, request, send_file
import io
import pandas as pd
import logging
from app.models.db import get_db_session
from app.models.models import Attendance
from datetime import datetime
from app.serializers import (
    AttendanceSerializer,
    json_response,
    error_json_response,
    handle_serialization_errors,
)

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

        session = get_db_session()
        attendance_query = session.query(Attendance).order_by(Attendance.date.desc())
        attendance_records = attendance_query.all()

        # Serializer를 사용한 데이터 직렬화
        serialized_records = AttendanceSerializer.serialize_attendances(
            attendance_records
        )

        session.close()

        # JSON 응답 (기본값)
        if format_type == "json":
            return json_response(
                data=serialized_records,
                message="출퇴근 기록 조회 성공",
                status_code=200,
            )

        # Excel 파일 다운로드
        elif format_type == "excel":
            # Excel 생성을 위한 데이터 변환
            records_data = [
                (
                    record.id,
                    record.date.strftime("%Y-%m-%d") if record.date else None,
                    record.instructor,
                    record.training_course,
                    (
                        record.check_in_time.strftime("%H:%M")
                        if record.check_in_time
                        else None
                    ),
                    (
                        record.check_out_time.strftime("%H:%M")
                        if record.check_out_time
                        else None
                    ),
                    record.daily_log,
                )
                for record in attendance_records
            ]

            columns = [
                "ID",
                "날짜",
                "강사",
                "훈련과정",
                "출근 시간",
                "퇴근 시간",
                "일지 작성 완료",
            ]
            df = pd.DataFrame(records_data, columns=columns)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="출퇴근 기록")
            output.seek(0)
            return send_file(
                output,
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
        data = request.json
        if not data:
            return error_json_response("요청 데이터가 없습니다.", status_code=400)

        # 스키마를 사용한 데이터 검증
        validated_data = AttendanceSerializer.deserialize_attendance_create(data)

        session = get_db_session()
        try:
            # 시간 문자열을 Time 객체로 변환
            check_in_time = (
                datetime.strptime(
                    validated_data.get("check_in_time", ""), "%H:%M"
                ).time()
                if validated_data.get("check_in_time")
                else None
            )
            check_out_time = (
                datetime.strptime(
                    validated_data.get("check_out_time", ""), "%H:%M"
                ).time()
                if validated_data.get("check_out_time")
                else None
            )

            attendance = Attendance(
                date=validated_data["date"],
                instructor=validated_data.get("instructor"),
                instructor_name=validated_data.get("instructor_name"),
                training_course=validated_data.get("training_course"),
                check_in_time=check_in_time,
                check_out_time=check_out_time,
                daily_log=validated_data.get("daily_log", False),
            )

            session.add(attendance)
            session.commit()

            # 저장된 데이터 직렬화
            serialized_attendance = AttendanceSerializer.serialize_attendance(
                attendance
            )

        except Exception as e:
            session.rollback()
            logger.error(f"출퇴근 기록 저장 중 오류: {str(e)}")
            return error_json_response("출퇴근 기록 저장 실패", status_code=500)
        finally:
            session.close()

        return json_response(
            data=serialized_attendance,
            message="출퇴근 기록 저장 성공!",
            status_code=201,
        )
    except Exception as e:
        logger.error("Error saving attendance", exc_info=True)
        return error_json_response("출퇴근 기록 저장 실패", status_code=500)
