from typing import Any, Dict, List
from functools import wraps
from marshmallow import ValidationError, Schema
from flask import jsonify

from .base import ResponseSerializer


# ============================================================================
# Flask 응답 헬퍼 함수들
# ============================================================================


def json_response(data: Any, message: str = "성공", status_code: int = 200) -> tuple:
    """
    JSON 응답 생성

    Args:
        data: 응답 데이터
        message: 응답 메시지
        status_code: HTTP 상태 코드

    Returns:
        Flask 응답 튜플
    """
    response = ResponseSerializer.success_response(data=data, message=message)
    return jsonify(response), status_code


def error_json_response(
    error: str, details: Dict = None, status_code: int = 400
) -> tuple:
    """
    에러 JSON 응답 생성

    Args:
        error: 에러 메시지
        details: 상세 에러 정보
        status_code: HTTP 상태 코드

    Returns:
        Flask 응답 튜플
    """
    response = ResponseSerializer.error_response(
        error=error, details=details, status_code=status_code
    )
    return jsonify(response), status_code


def pagination_json_response(
    items: List[Any],
    page: int,
    per_page: int,
    total: int,
    schema: Schema,
    message: str = "성공",
) -> tuple:
    """
    페이지네이션 JSON 응답 생성

    Args:
        items: 아이템 리스트
        page: 현재 페이지
        per_page: 페이지당 아이템 수
        total: 전체 아이템 수
        schema: 직렬화할 스키마
        message: 응답 메시지

    Returns:
        Flask 응답 튜플
    """
    response = ResponseSerializer.pagination_response(
        items=items, page=page, per_page=per_page, total=total, schema=schema
    )
    response["message"] = message
    return jsonify(response), 200


# ============================================================================
# 예외 처리 데코레이터
# ============================================================================


def handle_serialization_errors(func):
    """
    직렬화/역직렬화 에러를 처리하는 데코레이터
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            return error_json_response(
                error="데이터 검증 실패", details=e.messages, status_code=400
            )
        except Exception as e:
            return error_json_response(
                error="서버 내부 오류", details={"detail": str(e)}, status_code=500
            )

    return wrapper
