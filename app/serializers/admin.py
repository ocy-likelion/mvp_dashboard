"""
Admin-related serialization and validation
"""

from typing import Dict, List
from .base import Serializer
from app.schemas import date_filter_schema, task_status_response_schema, combined_task_status_response_schema

class AdminSerializer(Serializer):
    """관리자 관련 데이터 직렬화/역직렬화"""

    @staticmethod
    def deserialize_date_filter(query_params: Dict) -> Dict:
        """날짜 필터 파라미터 검증 및 변환"""
        return Serializer.deserialize(query_params, date_filter_schema)

    @staticmethod
    def serialize_task_status(task_status_data: Dict) -> Dict:
        """업무 체크 상태 직렬화"""
        return Serializer.serialize(task_status_data, task_status_response_schema)

    @staticmethod
    def serialize_combined_task_status(task_status_list: List[Dict]) -> List[Dict]:
        """통합 업무 체크 상태 직렬화"""
        return [Serializer.serialize(item, combined_task_status_response_schema) for item in task_status_list]
