"""
Attendance service for attendance-related business logic
"""

from typing import Dict, List
from datetime import datetime, time
from sqlalchemy.orm import Session

import io
import pandas as pd
from .base_service import BaseService
from app.models.models import Attendance


class AttendanceService(BaseService):
    """출석 관련 비즈니스 로직 처리"""

    @staticmethod
    def create_attendance(session: Session, attendance_data: Dict) -> Attendance:
        """출퇴근 기록 저장"""
        BaseService.validate_db_session(session)

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

        # 중복 출석 기록 확인
        existing_attendance = (
            session.query(Attendance)
            .filter(
                Attendance.date == attendance_date,
                Attendance.instructor == attendance_data.get("instructor"),
                Attendance.training_course == attendance_data.get("training_course"),
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
    def get_attendance_records(session: Session, limit: int = None) -> List[Attendance]:
        """출퇴근 기록 조회"""
        BaseService.validate_db_session(session)

        query = session.query(Attendance).order_by(Attendance.date.desc())

        if limit:
            query = query.limit(limit)

        return query.all()

    @staticmethod
    def get_attendance_by_date_range(
        session: Session, start_date: datetime, end_date: datetime
    ) -> List[Attendance]:
        """기간별 출석 기록 조회"""
        BaseService.validate_db_session(session)

        return (
            session.query(Attendance)
            .filter(Attendance.date >= start_date, Attendance.date <= end_date)
            .order_by(Attendance.date.desc())
            .all()
        )

    @staticmethod
    def get_attendance_by_course(
        session: Session, training_course: str
    ) -> List[Attendance]:
        """교육과정별 출석 기록 조회"""
        BaseService.validate_db_session(session)

        return (
            session.query(Attendance)
            .filter(Attendance.training_course == training_course)
            .order_by(Attendance.date.desc())
            .all()
        )

    @staticmethod
    def get_attendance_by_instructor(
        session: Session, instructor: str
    ) -> List[Attendance]:
        """강사별 출석 기록 조회"""
        BaseService.validate_db_session(session)

        return (
            session.query(Attendance)
            .filter(Attendance.instructor == instructor)
            .order_by(Attendance.date.desc())
            .all()
        )

    @staticmethod
    def update_attendance(
        session: Session, attendance_id: int, update_data: Dict
    ) -> Attendance:
        """출석 기록 수정"""
        attendance = AttendanceService.safe_get_by_id(
            session, Attendance, attendance_id, "출석 기록을 찾을 수 없습니다."
        )

        # 시간 데이터 업데이트
        if "check_in_time" in update_data:
            if update_data["check_in_time"]:
                try:
                    attendance.check_in_time = datetime.strptime(
                        update_data["check_in_time"], "%H:%M"
                    ).time()
                except ValueError:
                    raise ValueError(
                        "출근 시간 형식이 올바르지 않습니다. HH:MM 형식을 사용해주세요."
                    )
            else:
                attendance.check_in_time = None

        if "check_out_time" in update_data:
            if update_data["check_out_time"]:
                try:
                    attendance.check_out_time = datetime.strptime(
                        update_data["check_out_time"], "%H:%M"
                    ).time()
                except ValueError:
                    raise ValueError(
                        "퇴근 시간 형식이 올바르지 않습니다. HH:MM 형식을 사용해주세요."
                    )
            else:
                attendance.check_out_time = None

        # 기타 필드 업데이트
        allowed_fields = [
            "instructor",
            "instructor_name",
            "training_course",
            "daily_log",
        ]
        for field, value in update_data.items():
            if field in allowed_fields and hasattr(attendance, field):
                setattr(attendance, field, value)

        return attendance

    @staticmethod
    def delete_attendance(session: Session, attendance_id: int) -> None:
        """출석 기록 삭제"""
        attendance = AttendanceService.safe_get_by_id(
            session, Attendance, attendance_id, "출석 기록을 찾을 수 없습니다."
        )
        session.delete(attendance)

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

    @staticmethod
    def get_attendance_summary(session: Session, training_course: str = None) -> Dict:
        """출석 요약 정보 조회"""
        BaseService.validate_db_session(session)

        query = session.query(Attendance)
        if training_course:
            query = query.filter(Attendance.training_course == training_course)

        attendances = query.all()

        total_records = len(attendances)
        records_with_log = sum(1 for att in attendances if att.daily_log)

        # 근무 시간 통계
        total_work_hours = 0
        valid_work_records = 0

        for att in attendances:
            if att.check_in_time and att.check_out_time:
                work_hours = AttendanceService.calculate_work_hours(
                    att.check_in_time, att.check_out_time
                )
                total_work_hours += work_hours
                valid_work_records += 1

        avg_work_hours = (
            total_work_hours / valid_work_records if valid_work_records > 0 else 0
        )

        return {
            "total_records": total_records,
            "records_with_daily_log": records_with_log,
            "daily_log_rate": (
                (records_with_log / total_records * 100) if total_records > 0 else 0
            ),
            "total_work_hours": round(total_work_hours, 2),
            "average_work_hours": round(avg_work_hours, 2),
            "valid_work_records": valid_work_records,
        }

    @staticmethod
    def get_latest_attendance(
        session: Session, training_course: str = None
    ) -> Attendance:
        """최근 출석 기록 조회"""
        BaseService.validate_db_session(session)

        query = session.query(Attendance)
        if training_course:
            query = query.filter(Attendance.training_course == training_course)

        return query.order_by(Attendance.date.desc()).first()
