from flask import Blueprint, request, jsonify, session
import logging
from app.models.db import get_db_connection

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
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
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"success": False, "message": "ID와 비밀번호를 입력하세요."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user or user[1] != password:
            return jsonify({"success": False, "message": "잘못된 ID 또는 비밀번호입니다."}), 401

        session.permanent = True  # 세션을 영구적으로 설정
        user_data = {"id": user[0], "username": username}
        session['user'] = user_data

        return jsonify({
            "success": True, 
            "message": "로그인 성공!",
            "user": user_data  # 사용자 정보 포함
        }), 200

    except Exception as e:
        logging.error("로그인 오류", exc_info=True)
        return jsonify({"success": False, "message": "서버 오류 발생"}), 500

@auth_bp.route('/logout', methods=['POST'])
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
    session.pop('user', None)
    return jsonify({"success": True, "message": "로그아웃 완료!"}), 200

@auth_bp.route('/me', methods=['GET'])
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
    if 'user' not in session:
        return jsonify({"success": False, "message": "로그인이 필요합니다."}), 401
    return jsonify({"success": True, "user": session['user']}), 200


@auth_bp.route('/user/change-password', methods=['POST'])
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
        username = data.get('username')
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not username or not current_password or not new_password:
            return jsonify({
                "success": False, 
                "message": "사용자명, 현재 비밀번호, 새 비밀번호를 모두 입력하세요."
            }), 400
            
        # 새 비밀번호 유효성 검사 (필요한 경우)
        if len(new_password) < 4:
            return jsonify({
                "success": False,
                "message": "새 비밀번호는 최소 4자 이상이어야 합니다."
            }), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 현재 비밀번호 확인
        cursor.execute(
            "SELECT id FROM users WHERE username = %s AND password = %s",
            (username, current_password)
        )
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return jsonify({
                "success": False,
                "message": "사용자명 또는 현재 비밀번호가 일치하지 않습니다."
            }), 401
            
        # 비밀번호 업데이트
        cursor.execute(
            "UPDATE users SET password = %s WHERE username = %s AND password = %s",
            (new_password, username, current_password)
        )
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({
                "success": False,
                "message": "비밀번호 변경에 실패했습니다."
            }), 500
            
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "비밀번호가 성공적으로 변경되었습니다."
        }), 200
        
    except Exception as e:
        logging.error("비밀번호 변경 오류", exc_info=True)
        return jsonify({
            "success": False,
            "message": "비밀번호 변경 중 오류가 발생했습니다."
        }), 500