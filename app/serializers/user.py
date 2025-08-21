from typing import Dict

from .base import Serializer
from app.schemas import (
    user_schema,
    user_login_schema,
    password_change_schema,
)


class UserSerializer:
    """사용자 관련 직렬화 함수들"""

    @staticmethod
    def serialize_user(user) -> Dict:
        """사용자 데이터 직렬화"""
        return Serializer.serialize(user, user_schema)

    @staticmethod
    def deserialize_user_login(data: Dict) -> Dict:
        """로그인 데이터 역직렬화"""
        return Serializer.deserialize(data, user_login_schema)

    @staticmethod
    def deserialize_password_change(data: Dict) -> Dict:
        """비밀번호 변경 데이터 역직렬화"""
        return Serializer.deserialize(data, password_change_schema)
