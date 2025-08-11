import bcrypt
import re
from typing import Tuple


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


def is_hashed_password(password: str) -> bool:
    """
    비밀번호가 이미 해싱되어 있는지 확인합니다.

    Args:
        password (str): 확인할 비밀번호

    Returns:
        bool: 해싱된 비밀번호이면 True, 평문이면 False
    """
    # bcrypt 해시는 항상 $2b$로 시작하고 특정 길이를 가집니다
    return password.startswith("$2b$") and len(password) == 60
