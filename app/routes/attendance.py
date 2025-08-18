from flask import Blueprint, request, send_file
import io
import pandas as pd
import logging
from app.models.db import get_db_session

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

        # Serializer를 사용한 출퇴근 기록 조회
        serialized_records = AttendanceSerializer.get_attendance(session)

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
            # Excel 생성을 위한 데이터 변환 (직렬화된 데이터 사용)
            records_data = [
                (
                    record["id"],
                    record["date"],
                    record["instructor"],
                    record["training_course"],
                    record["check_in_time"],
                    record["check_out_time"],
                    record["daily_log"],
                )
                for record in serialized_records
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

        session = get_db_session()
        try:
            # Serializer를 사용한 출퇴근 기록 저장 (검증 포함)
            serialized_attendance = AttendanceSerializer.save_attendance(session, data)
            session.commit()

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
