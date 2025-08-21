"""
Attendance service for attendance-related business logic
"""

from typing import Dict, List
from datetime import datetime, time

import io
import pandas as pd
from .base_service import BaseService
from app.models.models import Attendance
from app.utils.database import db_session, db_session_read_only


class AttendanceService(BaseService):
    """출석 관련 비즈니스 로직 처리"""

    @staticmethod
    def create_attendance(attendance_data: Dict) -> Attendance:
        """출퇴근 기록 저장"""
        # 시간 문자열을 Time 객체로 변환
        check_in_time = None
        check_out_time = None

        if attendance_data.get("check_in_time"):
            try:
                check_in_time = datetime.strptime(
                    attendance_data["check_in_time"], "%H:%M"
                ).time()
            except ValueError:
                raise ValueError(
                    "출근 시간 형식이 올바르지 않습니다. HH:MM 형식을 사용해주세요."
                )

        if attendance_data.get("check_out_time"):
            try:
                check_out_time = datetime.strptime(
                    attendance_data["check_out_time"], "%H:%M"
                ).time()
            except ValueError:
                raise ValueError(
                    "퇴근 시간 형식이 올바르지 않습니다. HH:MM 형식을 사용해주세요."
                )

        # 날짜 유효성 검증
        attendance_date = attendance_data["date"]
        if isinstance(attendance_date, str):
            try:
                attendance_date = datetime.strptime(attendance_date, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(
                    "날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식을 사용해주세요."
                )

        with db_session() as session:
            # 중복 출석 기록 확인
            existing_attendance = (
                session.query(Attendance)
                .filter(
                    Attendance.date == attendance_date,
                    Attendance.instructor == attendance_data.get("instructor"),
                    Attendance.training_course
                    == attendance_data.get("training_course"),
                )
                .first()
            )

            if existing_attendance:
                raise ValueError("해당 날짜에 이미 출석 기록이 존재합니다.")

            attendance = Attendance(
                date=attendance_date,
                instructor=attendance_data.get("instructor"),
                instructor_name=attendance_data.get("instructor_name"),
                training_course=attendance_data.get("training_course"),
                check_in_time=check_in_time,
                check_out_time=check_out_time,
                daily_log=attendance_data.get("daily_log", False),
            )

            AttendanceService.flush_and_get_id(session, attendance)
            return attendance

    @staticmethod
    def generate_excel_file(serialized_records: List[Dict]) -> io.BytesIO:
        """출퇴근 기록 Excel 파일 생성"""
        if not serialized_records:
            raise ValueError("Excel 생성을 위한 데이터가 없습니다.")

        # Excel 생성을 위한 데이터 변환
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

        return output

    @staticmethod
    def get_attendance_records(limit: int = None) -> List[Attendance]:
        """출퇴근 기록 조회"""
        with db_session_read_only() as session:
            query = session.query(Attendance).order_by(Attendance.date.desc())

            if limit:
                query = query.limit(limit)

            return query.all()

    @staticmethod
    def calculate_work_hours(check_in_time: time, check_out_time: time) -> float:
        """근무 시간 계산 (시간 단위)"""
        if not check_in_time or not check_out_time:
            return 0.0

        # time을 datetime으로 변환하여 계산
        check_in_dt = datetime.combine(datetime.today(), check_in_time)
        check_out_dt = datetime.combine(datetime.today(), check_out_time)

        # 퇴근 시간이 출근 시간보다 이른 경우 (다음날로 간주)
        if check_out_dt <= check_in_dt:
            check_out_dt = check_out_dt.replace(day=check_out_dt.day + 1)

        work_duration = check_out_dt - check_in_dt
        return work_duration.total_seconds() / 3600  # 시간 단위로 반환
