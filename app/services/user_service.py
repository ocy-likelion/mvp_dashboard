"""
User service for user-related business logic
"""

import bcrypt
import re
from typing import Dict, Tuple
from sqlalchemy.orm import Session

from .base_service import BaseService
from app.models.models import User


class UserService(BaseService):
    """사용자 관련 비즈니스 로직 처리"""

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
    def login(session: Session, validated_data: Dict) -> Dict:
        """로그인 처리"""
        UserService.validate_session(session)

        username = validated_data["username"]
        password = validated_data["password"]

        # 사용자 조회
        user = session.query(User).filter(User.username == username).first()

        if not user:
            raise ValueError("잘못된 ID 또는 비밀번호입니다.")

        # 비밀번호 검증 (bcrypt 사용)
        if not UserService.verify_password(password, user.password):
            raise ValueError("잘못된 ID 또는 비밀번호입니다.")

        return {"user_id": user.id, "username": user.username}

    @staticmethod
    def change_password(session: Session, validated_data: Dict) -> User:
        """비밀번호 변경"""
        UserService.validate_session(session)

        username = validated_data["username"]
        current_password = validated_data["current_password"]
        new_password = validated_data["new_password"]

        # 현재 비밀번호 확인
        user = session.query(User).filter(User.username == username).first()

        if not user:
            raise ValueError("사용자명 또는 현재 비밀번호가 일치하지 않습니다.")

        # 현재 비밀번호 검증 (bcrypt 사용)
        if not UserService.verify_password(current_password, user.password):
            raise ValueError("사용자명 또는 현재 비밀번호가 일치하지 않습니다.")

        # 새 비밀번호 강도 검증
        is_valid, error_message = UserService.validate_password_strength(new_password)
        if not is_valid:
            raise ValueError(error_message)

        # 새 비밀번호 해싱
        hashed_new_password = UserService.hash_password(new_password)

        user.password = hashed_new_password
        return user

    @staticmethod
    def create_user(session: Session, user_data: Dict) -> User:
        """사용자 생성"""
        UserService.validate_session(session)

        # 사용자명 중복 확인
        existing_user = (
            session.query(User).filter(User.username == user_data["username"]).first()
        )
        if existing_user:
            raise ValueError("이미 존재하는 사용자명입니다.")

        # 비밀번호 강도 검증
        password = user_data.get("password", "")
        is_valid, error_message = UserService.validate_password_strength(password)
        if not is_valid:
            raise ValueError(error_message)

        # 비밀번호 해싱
        hashed_password = UserService.hash_password(password)

        # 사용자 생성
        user = User(
            username=user_data["username"],
            password=hashed_password,
            # 다른 필드들도 필요에 따라 추가
        )

        UserService.flush_and_get_id(session, user)
        return user

    @staticmethod
    def get_user_by_username(session: Session, username: str) -> User:
        """사용자명으로 사용자 조회"""
        UserService.validate_session(session)

        user = session.query(User).filter(User.username == username).first()
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다.")

        return user

    @staticmethod
    def update_user(session: Session, user_id: int, update_data: Dict) -> User:
        """사용자 정보 업데이트"""
        user = UserService.safe_get_by_id(
            session, User, user_id, "사용자를 찾을 수 없습니다."
        )

        # 업데이트할 필드들 적용
        for field, value in update_data.items():
            if hasattr(user, field) and field != "password":  # 비밀번호는 별도 메서드로
                setattr(user, field, value)

        return user
