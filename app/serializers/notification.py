from typing import Dict

from .base import Serializer
from app.schemas import notification_query_schema


class NotificationSerializer:
    """알림 관련 직렬화 함수들"""

    @staticmethod
    def deserialize_notification_query(data: Dict) -> Dict:
        """알림 조회 데이터 역직렬화"""
        return Serializer.deserialize(data, notification_query_schema)
