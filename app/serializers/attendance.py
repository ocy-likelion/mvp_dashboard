from typing import Dict, List
from datetime import datetime

from .base import Serializer
from app.schemas import (
    attendance_schema,
    attendances_schema,
    attendance_create_schema,
)
from app.models.models import Attendance


class AttendanceSerializer:
    """출석 관련 직렬화 함수들"""

    @staticmethod
    def serialize_attendance(attendance) -> Dict:
        """단일 출석 직렬화"""
        return Serializer.serialize(attendance, attendance_schema)

    @staticmethod
    def serialize_attendances(attendances: List) -> List[Dict]:
        """여러 출석 직렬화"""
        return Serializer.serialize(attendances, attendances_schema, many=True)

    @staticmethod
    def deserialize_attendance_create(data: Dict) -> Dict:
        """출석 생성 데이터 역직렬화"""
        return Serializer.deserialize(data, attendance_create_schema)

    @staticmethod
    def save_attendance(session, data: Dict):
        """출퇴근 기록 저장"""
        # 데이터 검증
        validated_data = AttendanceSerializer.deserialize_attendance_create(data)

        # 시간 문자열을 Time 객체로 변환
        check_in_time = (
            datetime.strptime(validated_data.get("check_in_time", ""), "%H:%M").time()
            if validated_data.get("check_in_time")
            else None
        )
        check_out_time = (
            datetime.strptime(validated_data.get("check_out_time", ""), "%H:%M").time()
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
        session.flush()  # ID를 얻기 위해 flush

        # 저장된 데이터 직렬화
        return AttendanceSerializer.serialize_attendance(attendance)

    @staticmethod
    def get_attendance(session) -> List[Dict]:
        """출퇴근 기록 조회"""
        attendance_query = session.query(Attendance).order_by(Attendance.date.desc())
        attendance_records = attendance_query.all()

        # Serializer를 사용한 데이터 직렬화
        return AttendanceSerializer.serialize_attendances(attendance_records)
