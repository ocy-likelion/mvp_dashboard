from typing import Dict, List

from .base import Serializer
from app.schemas import (
    task_items_schema,
    task_update_schema,
    irregular_task_create_schema,
    task_filter_schema,
)


class TaskSerializer:
    """작업 관련 직렬화 함수들"""

    @staticmethod
    def deserialize_task_filter(query_params: Dict) -> Dict:
        """작업 필터 파라미터 검증 및 변환"""
        return Serializer.deserialize(query_params, task_filter_schema)

    @staticmethod
    def serialize_task_items(task_items: List) -> List[Dict]:
        """여러 작업 항목 직렬화"""
        return Serializer.serialize(task_items, task_items_schema, many=True)

    @staticmethod
    def deserialize_task_update(data: Dict) -> Dict:
        """작업 체크리스트 업데이트 데이터 역직렬화"""
        return Serializer.deserialize(data, task_update_schema)

    @staticmethod
    def deserialize_irregular_task_create(data: Dict) -> Dict:
        """불규칙 업무 생성 데이터 역직렬화"""
        return Serializer.deserialize(data, irregular_task_create_schema)

    @staticmethod
    def serialize_task_update_result(result: Dict) -> Dict:
        """작업 업데이트 결과 직렬화"""
        updated_count = result["updated_count"]
        not_found_items = result["not_found_items"]

        response_data = {
            "updated_count": updated_count,
        }

        if not_found_items:
            response_data["warning"] = (
                "일부 항목은 당일 저장된 데이터가 없어 업데이트되지 않았습니다."
            )
            response_data["not_found_items"] = not_found_items

        return response_data
