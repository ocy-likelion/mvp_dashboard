from typing import Dict, List

from .base import Serializer
from app.schemas import (
    training_info_schema,
    training_infos_schema,
    training_info_create_schema,
    training_info_update_schema,
)


class TrainingSerializer:
    """교육 관련 직렬화 함수들"""

    @staticmethod
    def deserialize_training_info_create(data: Dict) -> Dict:
        """교육 정보 생성 데이터 역직렬화"""
        return Serializer.deserialize(data, training_info_create_schema)
