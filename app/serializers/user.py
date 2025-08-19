from typing import Dict, List, Tuple
import bcrypt
import re

from .base import Serializer
from app.schemas import (
    user_schema,
    users_schema,
    user_create_schema,
    user_update_schema,
    user_login_schema,
    password_change_schema,
)
from app.models.models import User


class UserSerializer:
    """사용자 관련 직렬화 함수들"""

    @staticmethod
    def serialize_user(user) -> Dict:
        """단일 사용자 직렬화"""
        return Serializer.serialize(user, user_schema)

    @staticmethod
    def serialize_users(users: List) -> List[Dict]:
        """여러 사용자 직렬화"""
        return Serializer.serialize(users, users_schema, many=True)

    @staticmethod
    def deserialize_user_create(data: Dict) -> Dict:
        """사용자 생성 데이터 역직렬화"""
        return Serializer.deserialize(data, user_create_schema)

    @staticmethod
    def deserialize_user_update(data: Dict) -> Dict:
        """사용자 수정 데이터 역직렬화"""
        return Serializer.deserialize(data, user_update_schema, partial=True)

    @staticmethod
    def deserialize_user_login(data: Dict) -> Dict:
        """로그인 데이터 역직렬화"""
        return Serializer.deserialize(data, user_login_schema)

    @staticmethod
    def deserialize_password_change(data: Dict) -> Dict:
        """비밀번호 변경 데이터 역직렬화"""
        return Serializer.deserialize(data, password_change_schema)

    # 비밀번호 관련 유틸리티 함수들
    @staticmethod
    def hash_password(password: str) -> str:
        """
        비밀번호를 bcrypt로 해싱합니다.

        Args:
            password (str): 해싱할 평문 비밀번호

        Returns:
            str: 해싱된 비밀번호 (bytes를 문자열로 인코딩)
        """
        # 비밀번호를 bytes로 인코딩
        password_bytes = password.encode("utf-8")
        # bcrypt로 해싱 (기본 라운드: 12)
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
        # bytes를 문자열로 디코딩하여 반환
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        평문 비밀번호와 해싱된 비밀번호를 비교하여 검증합니다.

        Args:
            password (str): 검증할 평문 비밀번호
            hashed_password (str): 데이터베이스에 저장된 해싱된 비밀번호

        Returns:
            bool: 비밀번호가 일치하면 True, 아니면 False
        """
        try:
            # 문자열을 bytes로 인코딩
            password_bytes = password.encode("utf-8")
            hashed_bytes = hashed_password.encode("utf-8")
            # bcrypt로 검증
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            # 인코딩 오류나 기타 예외 발생 시 False 반환
            return False

    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, str]:
        """
        비밀번호 강도를 검증합니다.

        Args:
            password (str): 검증할 비밀번호

        Returns:
            Tuple[bool, str]: (유효성 여부, 오류 메시지)
        """
        if len(password) < 8:
            return False, "비밀번호는 최소 8자 이상이어야 합니다."

        if not re.search(r"[A-Z]", password):
            return False, "비밀번호는 대문자를 포함해야 합니다."

        if not re.search(r"[a-z]", password):
            return False, "비밀번호는 소문자를 포함해야 합니다."

        if not re.search(r"\d", password):
            return False, "비밀번호는 숫자를 포함해야 합니다."

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "비밀번호는 특수문자를 포함해야 합니다."

        return True, ""

    @staticmethod
    def is_hashed_password(password: str) -> bool:
        """비밀번호가 이미 해시되었는지 확인"""
        return password.startswith("$2b$")

    @staticmethod
    def login(session, data: Dict) -> Dict:
        """로그인 처리"""
        # 데이터 검증
        validated_data = UserSerializer.deserialize_user_login(data)

        # 사용자 조회
        user = (
            session.query(User)
            .filter(User.username == validated_data["username"])
            .first()
        )

        if not user:
            raise ValueError("잘못된 ID 또는 비밀번호입니다.")

        # 비밀번호 검증 (bcrypt 사용)
        if not UserSerializer.verify_password(
            validated_data["password"], user.password
        ):
            raise ValueError("잘못된 ID 또는 비밀번호입니다.")

        return {"user_id": user.id, "username": user.username}

    @staticmethod
    def change_password(session, data: Dict):
        """비밀번호 변경"""
        # 데이터 검증
        validated_data = UserSerializer.deserialize_password_change(data)

        # 현재 비밀번호 확인
        user = (
            session.query(User)
            .filter(User.username == validated_data["username"])
            .first()
        )

        if not user:
            raise ValueError("사용자명 또는 현재 비밀번호가 일치하지 않습니다.")

        # 현재 비밀번호 검증 (bcrypt 사용)
        if not UserSerializer.verify_password(
            validated_data["current_password"], user.password
        ):
            raise ValueError("사용자명 또는 현재 비밀번호가 일치하지 않습니다.")

        # 새 비밀번호 해싱
        hashed_new_password = UserSerializer.hash_password(
            validated_data["new_password"]
        )

        user.password = hashed_new_password
        return user
