from flask import Blueprint, request, session, jsonify
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
    사용자 로그인 API
    ---
    tags:
      - Authentication
    summary: 사용자 로그인 및 세션 생성
    description: |
      사용자명과 비밀번호를 받아 로그인을 처리합니다.
      로그인 성공 시 세션 쿠키가 자동으로 설정됩니다.
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // 세션 쿠키 포함
        body: JSON.stringify({
          username: 'user123',
          password: 'password123'
        })
      });
      
      const result = await response.json();
      console.log(result);
      ```
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
              description: 사용자명
              example: "user123"
            password:
              type: string
              description: 비밀번호
              example: "password123"
    responses:
      200:
        description: 로그인 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "로그인 성공!"
            data:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                username:
                  type: string
                  example: "user123"
                name:
                  type: string
                  example: "홍길동"
                role:
                  type: string
                  example: "user"
        examples:
          application/json:
            summary: 로그인 성공 응답
            value:
              success: true
              message: "로그인 성공!"
              data:
                id: 1
                username: "user123"
                name: "홍길동"
                role: "user"
      400:
        description: 필수 데이터 누락 또는 유효성 검사 실패
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "사용자명과 비밀번호를 입력해주세요."
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 400
      401:
        description: 잘못된 ID 또는 비밀번호
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "잘못된 사용자명 또는 비밀번호입니다."
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 401
      500:
        description: 서버 오류
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "서버 오류 발생"
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 500
    """
    try:
        validated_data = UserSerializer.deserialize_user_login(request.json)
        user = UserService.login(validated_data)
        # 기존 함수와 동일한 구조로 사용자 데이터 생성
        user_data = {"id": user.id, "username": user.username}
        session.permanent = True  # 세션을 영구적으로 설정
        session["user"] = user_data

        return jsonify({
            "success": True, 
            "message": "로그인 성공!",
            "user": user_data  # 기존 함수와 동일한 구조
        }), 200

    except ValueError as e:
        logger.warning(f"로그인 실패: {str(e)}")
        return error_json_response(str(e), status_code=400)
    except Exception as e:
        logger.error("로그인 오류", exc_info=True)
        return error_json_response("서버 오류 발생", status_code=500)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """
    사용자 로그아웃 API
    ---
    tags:
      - Authentication
    summary: 사용자 로그아웃 및 세션 삭제
    description: |
      현재 로그인된 사용자의 세션을 삭제합니다.
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/logout', {
        method: 'POST',
        credentials: 'include' // 세션 쿠키 포함
      });
      
      const result = await response.json();
      console.log(result);
      ```
    responses:
      200:
        description: 로그아웃 완료
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "로그아웃 완료!"
            data:
              type: null
              example: null
        examples:
          application/json:
            summary: 로그아웃 성공 응답
            value:
              success: true
              message: "로그아웃 완료!"
              data: null
    """
    session.pop("user", None)
    return jsonify({"success": True, "message": "로그아웃 완료!"}), 200


@auth_bp.route("/me", methods=["GET"])
def get_current_user():
    """
    현재 로그인된 사용자 정보 조회 API
    ---
    tags:
      - Authentication
    summary: 현재 로그인된 사용자 정보 반환
    description: |
      현재 세션에 로그인된 사용자의 정보를 반환합니다.
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/me', {
        method: 'GET',
        credentials: 'include' // 세션 쿠키 포함
      });
      
      const result = await response.json();
      console.log(result);
      ```
    responses:
      200:
        description: 현재 로그인된 사용자 정보 반환
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "사용자 정보 조회 성공"
            data:
              type: object
              properties:
                user:
                  type: object
                  properties:
                    id:
                      type: integer
                      example: 1
                    username:
                      type: string
                      example: "user123"
                    name:
                      type: string
                      example: "홍길동"
                    role:
                      type: string
                      example: "user"
        examples:
          application/json:
            summary: 사용자 정보 조회 성공 응답
            value:
              success: true
              message: "사용자 정보 조회 성공"
              data:
                user:
                  id: 1
                  username: "user123"
                  name: "홍길동"
                  role: "user"
      401:
        description: 로그인 필요
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "로그인이 필요합니다."
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 401
    """
    if "user" not in session:
        return jsonify({"success": False, "message": "로그인이 필요합니다."}), 401
    return jsonify({"success": True, "user": session["user"]}), 200


@auth_bp.route("/user/change-password", methods=["POST"])
@handle_serialization_errors
def change_password():
    """
    사용자 비밀번호 변경 API
    ---
    tags:
      - Authentication
    summary: 사용자 비밀번호 변경
    description: |
      현재 비밀번호를 확인하고 새로운 비밀번호로 변경합니다.
      
      ### API 명세
      **POST** `/user/change-password`
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/user/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          username: 'user123',
          current_password: 'oldpassword123',
          new_password: 'newpassword123'
        })
      });
      
      const result = await response.json();
      console.log(result);
      ```
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
              description: 사용자명
              example: "user123"
            current_password:
              type: string
              description: 현재 비밀번호
              example: "oldpassword123"
            new_password:
              type: string
              description: 새로운 비밀번호
              example: "newpassword123"
    responses:
      200:
        description: 비밀번호 변경 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "비밀번호가 성공적으로 변경되었습니다."
        examples:
          application/json:
            summary: 비밀번호 변경 성공 응답
            value:
              success: true
              message: "비밀번호가 성공적으로 변경되었습니다."
      400:
        description: 필수 데이터 누락 또는 유효성 검사 실패
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "모든 필드를 입력해주세요."
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 400
      401:
        description: 현재 비밀번호가 일치하지 않음
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "현재 비밀번호가 일치하지 않습니다."
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 401
      500:
        description: 서버 오류 발생
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "비밀번호 변경 중 오류가 발생했습니다."
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 500
    """
    try:
        validated_data = UserSerializer.deserialize_password_change(request.json)
        UserService.change_password(validated_data)

        return jsonify({
            "success": True,
            "message": "비밀번호가 성공적으로 변경되었습니다."
        }), 200

    except Exception as e:
        logger.error("비밀번호 변경 오류", exc_info=True)
        return error_json_response(
            "비밀번호 변경 중 오류가 발생했습니다.", status_code=500
        )
