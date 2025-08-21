from flask import Blueprint, request, session
import logging

from app.serializers import (
    UserSerializer,
    json_response,
    error_json_response,
    handle_serialization_errors,
)
from app.services import UserService

auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


@auth_bp.route("/login", methods=["POST"])
@handle_serialization_errors
def login():
    """
    로그인 API
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
            password:
              type: string
    responses:
      200:
        description: 로그인 성공
      400:
        description: 필수 데이터 누락
      401:
        description: 잘못된 ID 또는 비밀번호
      500:
        description: 서버 오류
    """
    try:
        validated_data = UserSerializer.deserialize_user_login(request.json)
        user = UserService.login(validated_data)
        serialized_user = UserSerializer.serialize_user(user)

        session.permanent = True  # 세션을 영구적으로 설정
        session["user"] = serialized_user

        return json_response(
            data=serialized_user, message="로그인 성공!", status_code=200
        )

    except Exception as e:
        logger.error("로그인 오류", exc_info=True)
        return error_json_response("서버 오류 발생", status_code=500)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """
    로그아웃 API
    ---
    tags:
      - Authentication
    responses:
      200:
        description: 로그아웃 완료
    """
    session.pop("user", None)
    return json_response(data=None, message="로그아웃 완료!", status_code=200)


@auth_bp.route("/me", methods=["GET"])
def get_current_user():
    """
    로그인 상태 확인 API
    ---
    tags:
      - Authentication
    responses:
      200:
        description: 현재 로그인된 사용자 정보 반환
      401:
        description: 로그인 필요
    """
    if "user" not in session:
        return error_json_response("로그인이 필요합니다.", status_code=401)
    return json_response(data={"user": session["user"]}, status_code=200)


@auth_bp.route("/user/change-password", methods=["POST"])
@handle_serialization_errors
def change_password():
    """
    사용자 비밀번호 변경 API
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - username
            - current_password
            - new_password
          properties:
            username:
              type: string
              example: "user123"
            current_password:
              type: string
              example: "current123"
            new_password:
              type: string
              example: "new123"
    responses:
      200:
        description: 비밀번호 변경 성공
      400:
        description: 필수 데이터 누락
      401:
        description: 현재 비밀번호가 일치하지 않음
      500:
        description: 서버 오류 발생
    """
    try:
        validated_data = UserSerializer.deserialize_password_change(request.json)
        UserService.change_password(validated_data)

        return json_response(
            data=None,
            message="비밀번호가 성공적으로 변경되었습니다.",
            status_code=200,
        )

    except Exception as e:
        logger.error("비밀번호 변경 오류", exc_info=True)
        return error_json_response(
            "비밀번호 변경 중 오류가 발생했습니다.", status_code=500
        )
