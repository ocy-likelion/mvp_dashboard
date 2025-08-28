from typing import Dict, List

from .base import Serializer
from app.schemas import (
    attendance_schema,
    attendances_schema,
    attendance_create_schema,
    attendance_list_filter_schema,
)


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
    def deserialize_attendance_list_get(query_params: Dict) -> Dict:
        """출퇴근 기록 목록 조회 쿼리 파라미터 검증 및 변환"""
        return Serializer.deserialize(query_params, attendance_list_filter_schema)
