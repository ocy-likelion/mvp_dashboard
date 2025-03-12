from flask import Blueprint, request, jsonify, session
from app.database import get_db_connection
import logging

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['POST'])
def login():
    """
    로그인 API
    ---
    tags:
      - Authentication
    summary: 사용자 로그인
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
      401:
        description: 로그인 실패
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

        session['user'] = {"id": user[0], "username": username}
        return jsonify({"success": True, "message": "로그인 성공!", "username": username}), 200

    except Exception as e:
        logging.error("로그인 오류", exc_info=True)
        return jsonify({"success": False, "message": "서버 오류 발생"}), 500

@bp.route('/logout', methods=['POST'])
def logout():
    """
    로그아웃 API
    ---
    tags:
      - Authentication
    responses:
      200:
        description: 로그아웃 성공
    """
    session.pop('user', None)
    return jsonify({"success": True, "message": "로그아웃 완료!"}), 200

@bp.route('/me', methods=['GET'])
def get_current_user():
    """
    현재 사용자 정보 조회 API
    ---
    tags:
      - Authentication
    responses:
      200:
        description: 현재 로그인된 사용자 정보
      401:
        description: 로그인 필요
    """
    if 'user' not in session:
        return jsonify({"success": False, "message": "로그인이 필요합니다."}), 401
    return jsonify({"success": True, "user": session['user']}), 200 