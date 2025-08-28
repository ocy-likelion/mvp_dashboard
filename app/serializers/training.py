from typing import Dict, List

from .base import Serializer
from app.schemas import (
    training_info_schema,
    training_infos_schema,
    training_info_create_schema,
)


class TrainingSerializer:
    """교육 관련 직렬화 함수들"""

    @staticmethod
    def serialize_training_info(training_data) -> List[Dict]:
        """교육 정보 직렬화 (단일 또는 다중)"""
        if isinstance(training_data, list):
            return Serializer.serialize(training_data, training_infos_schema, many=True)
        else:
            return [Serializer.serialize(training_data, training_info_schema)]

    @staticmethod
    def deserialize_training_info_create(data: Dict) -> Dict:
        """교육 정보 생성 데이터 역직렬화"""
        return Serializer.deserialize(data, training_info_create_schema)
