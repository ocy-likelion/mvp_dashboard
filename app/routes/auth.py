from flask import Blueprint, request, jsonify, session
import logging
from app.models.db import get_db_session
from app.models.models import User
from app.utils.password import (
    hash_password,
    verify_password,
    validate_password_strength,
)

auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


@auth_bp.route("/login", methods=["POST"])
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
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return (
            jsonify({"success": False, "message": "ID와 비밀번호를 입력하세요."}),
            400,
        )

    try:
        session_db = get_db_session()
        try:
            # 사용자 조회
            user = session_db.query(User).filter(User.username == username).first()

            if not user:
                return (
                    jsonify(
                        {"success": False, "message": "잘못된 ID 또는 비밀번호입니다."}
                    ),
                    401,
                )

            # 비밀번호 검증 (bcrypt 사용)
            if not verify_password(password, user.password):
                return (
                    jsonify(
                        {"success": False, "message": "잘못된 ID 또는 비밀번호입니다."}
                    ),
                    401,
                )

        finally:
            session_db.close()

        session.permanent = True  # 세션을 영구적으로 설정
        user_data = {"id": user.id, "username": username}
        session["user"] = user_data

        return (
            jsonify(
                {
                    "success": True,
                    "message": "로그인 성공!",
                    "user": user_data,  # 사용자 정보 포함
                }
            ),
            200,
        )

    except Exception as e:
        logger.error("로그인 오류", exc_info=True)
        return jsonify({"success": False, "message": "서버 오류 발생"}), 500


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
    return jsonify({"success": True, "message": "로그아웃 완료!"}), 200


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
        return jsonify({"success": False, "message": "로그인이 필요합니다."}), 401
    return jsonify({"success": True, "user": session["user"]}), 200


@auth_bp.route("/user/change-password", methods=["POST"])
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
        data = request.json
        username = data.get("username")
        current_password = data.get("current_password")
        new_password = data.get("new_password")

        if not username or not current_password or not new_password:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "사용자명, 현재 비밀번호, 새 비밀번호를 모두 입력하세요.",
                    }
                ),
                400,
            )

        # 새 비밀번호 강도 검증
        is_valid, error_message = validate_password_strength(new_password)
        if not is_valid:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": error_message,
                    }
                ),
                400,
            )

        session_db = get_db_session()
        try:
            # 현재 비밀번호 확인
            user = session_db.query(User).filter(User.username == username).first()

            if not user:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "사용자명 또는 현재 비밀번호가 일치하지 않습니다.",
                        }
                    ),
                    401,
                )

            # 현재 비밀번호 검증 (bcrypt 사용)
            if not verify_password(current_password, user.password):
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "사용자명 또는 현재 비밀번호가 일치하지 않습니다.",
                        }
                    ),
                    401,
                )

            # 새 비밀번호 해싱
            hashed_new_password = hash_password(new_password)

            # 비밀번호 업데이트
            user.password = hashed_new_password
            session_db.commit()

            return (
                jsonify(
                    {"success": True, "message": "비밀번호가 성공적으로 변경되었습니다."}
                ),
                200,
            )

        finally:
            session_db.close()

    except Exception as e:
        logger.error("비밀번호 변경 오류", exc_info=True)
        return (
            jsonify(
                {"success": False, "message": "비밀번호 변경 중 오류가 발생했습니다."}
            ),
            500,
        )
