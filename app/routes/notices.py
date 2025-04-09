from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
from app.models.db import get_db_connection

notices_bp = Blueprint('notices', __name__)

@notices_bp.route('/notices', methods=['GET'])
def get_notices():
    """
    공지사항 조회 API
    ---
    tags:
      - Notices
    responses:
      200:
        description: 모든 공지사항 데이터를 포함한 응답
      500:
        description: 공지사항을 불러오는 데 실패함
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 'created_at' 대신 'date' 컬럼 사용
        cursor.execute("SELECT * FROM notices WHERE is_deleted = FALSE ORDER BY date DESC")
        
        # 결과를 딕셔너리 형태로 변환
        columns = ['id', 'type', 'title', 'content', 'date', 'created_by']
        notice_rows = cursor.fetchall()
        notices = []
        
        for row in notice_rows:
            notice_dict = {}
            for i, column in enumerate(columns):
                notice_dict[column] = row[i]
            notices.append(notice_dict)
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "data": notices
        }), 200
    except Exception as e:
        logging.error("Error retrieving notices", exc_info=True)
        return jsonify({"success": False, "message": "공지사항을 불러오는데 실패했습니다."}), 500

@notices_bp.route('/notices', methods=['POST'])
def add_notice():
    """
    공지사항 추가 API
    ---
    tags:
      - Notices
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - title
            - content
            - username
            - type
          properties:
            title:
              type: string
              example: "시스템 점검 안내"
            content:
              type: string
              example: "금일 오후 6시부터 8시까지 시스템 점검이 진행됩니다."
            username:
              type: string
              example: "홍길동"
            type:
              type: string
              example: "공지사항"
    responses:
      201:
        description: 공지사항 추가 성공
      400:
        description: 필수 데이터 누락
      500:
        description: 서버 오류 발생
    """
    try:
        data = request.json
        title = data.get("title")
        content = data.get("content")
        created_by = data.get("username")  # 프론트엔드에서 전달한 username 사용
        notice_type = data.get("type", "공지사항")  # 기본값은 "공지사항"으로 설정

        if not title or not content or not created_by:
            return jsonify({"success": False, "message": "제목, 내용, 작성자를 모두 입력하세요."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO notices (title, content, date, created_by, type)
            VALUES (%s, %s, %s, %s, %s)
        ''', (title, content, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), created_by, notice_type))
        
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "공지사항이 추가되었습니다."}), 201
    except Exception as e:
        logging.error("공지사항 추가 오류", exc_info=True)
        return jsonify({"success": False, "message": "공지사항 추가 실패"}), 500

@notices_bp.route('/notices/<int:notice_id>', methods=['PUT'])
def update_notice(notice_id):
    """
    공지사항 수정 API
    ---
    tags:
      - Notices
    parameters:
      - name: notice_id
        in: path
        type: integer
        required: true
        description: 수정할 공지사항 ID
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
              example: "수정된 공지사항 제목"
            content:
              type: string
              example: "수정된 공지사항 내용입니다."
            type:
              type: string
              example: "공지사항"
            username:
              type: string
              example: "홍길동"
    responses:
      200:
        description: 공지사항 수정 성공
      400:
        description: 필수 데이터 누락
      404:
        description: 공지사항을 찾을 수 없음
      500:
        description: 서버 오류 발생
    """
    try:
        data = request.json
        title = data.get('title')
        content = data.get('content')
        notice_type = data.get('type')
        username = data.get('username')  # 수정자 정보

        if not title or not content or not username:
            return jsonify({"success": False, "message": "제목, 내용, 사용자명을 모두 입력하세요."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 먼저 해당 공지사항이 존재하는지 확인
        cursor.execute("SELECT id FROM notices WHERE id = %s", (notice_id,))
        notice = cursor.fetchone()
        
        if not notice:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "해당 공지사항을 찾을 수 없습니다."}), 404
        
        # 공지사항 업데이트
        update_fields = ["title = %s", "content = %s", "date = NOW()"]
        params = [title, content]
        
        if notice_type:
            update_fields.append("type = %s")
            params.append(notice_type)
        
        # 수정자 정보 추가
        update_fields.append("modified_by = %s")
        params.append(username)
        
        params.append(notice_id)  # WHERE 조건용
        
        query = f"UPDATE notices SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(query, tuple(params))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"success": False, "message": "공지사항 수정에 실패했습니다."}), 500
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "공지사항이 성공적으로 수정되었습니다."}), 200
        
    except Exception as e:
        logging.error("공지사항 수정 오류", exc_info=True)
        return jsonify({"success": False, "message": "공지사항 수정 중 오류가 발생했습니다."}), 500

@notices_bp.route('/notices/<int:notice_id>', methods=['DELETE'])
def delete_notice(notice_id):
    """
    공지사항 삭제 API
    ---
    tags:
      - Notices
    parameters:
      - name: notice_id
        in: path
        type: integer
        required: true
        description: 삭제할 공지사항 ID
    responses:
      200:
        description: 공지사항 삭제 성공
      404:
        description: 공지사항을 찾을 수 없음
      500:
        description: 서버 오류 발생
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 공지사항 존재 확인
        cursor.execute("SELECT id FROM notices WHERE id = %s", (notice_id,))
        notice = cursor.fetchone()
        
        if not notice:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "해당 공지사항을 찾을 수 없습니다."}), 404
        
        # 실제 삭제 대신 is_deleted 필드 업데이트
        cursor.execute("UPDATE notices SET is_deleted = TRUE WHERE id = %s", (notice_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"success": False, "message": "공지사항 삭제에 실패했습니다."}), 500
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "공지사항이 성공적으로 삭제되었습니다."}), 200
        
    except Exception as e:
        logging.error("공지사항 삭제 오류", exc_info=True)
        return jsonify({"success": False, "message": "공지사항 삭제 중 오류가 발생했습니다."}), 500

@notices_bp.route('/notices/read', methods=['POST'])
def mark_notice_read():
    """
    공지사항 읽음 표시 API
    ---
    tags:
      - Notices
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - notice_id
            - username
          properties:
            notice_id:
              type: integer
              example: 1
            username:
              type: string
              example: "홍길동"
    responses:
      201:
        description: 읽음 표시 성공
      400:
        description: 필수 데이터 누락
      500:
        description: 서버 오류 발생
    """
    try:
        data = request.json
        notice_id = data.get("notice_id")
        username = data.get("username")

        if not notice_id or not username:
            return jsonify({"success": False, "message": "공지사항 ID와 사용자 이름이 필요합니다."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # ON CONFLICT DO NOTHING을 사용하여 동일한 사용자가 같은 공지를 여러 번 읽음 표시해도 에러가 나지 않도록 함
        cursor.execute('''
            INSERT INTO notice_reads (notice_id, username, read_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (notice_id, username) DO NOTHING
        ''', (notice_id, username))
        
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "공지사항 읽음 표시 완료"}), 201
    except Exception as e:
        logging.error("공지사항 읽음 표시 오류", exc_info=True)
        return jsonify({"success": False, "message": "공지사항 읽음 표시 실패"}), 500

@notices_bp.route('/notices/reads', methods=['GET'])
def get_notice_reads():
    """
    공지사항별 읽은 사용자 목록 조회 API
    ---
    tags:
      - Notices
    parameters:
      - name: notice_id
        in: query
        type: integer
        required: true
        description: "조회할 공지사항 ID"
    responses:
      200:
        description: 공지사항을 읽은 사용자 목록 반환
      400:
        description: 공지사항 ID 누락
      500:
        description: 서버 오류 발생
    """
    try:
        notice_id = request.args.get('notice_id')

        if not notice_id:
            return jsonify({"success": False, "message": "공지사항 ID가 필요합니다."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT username, read_at 
            FROM notice_reads 
            WHERE notice_id = %s 
            ORDER BY read_at DESC
        ''', (notice_id,))
        
        reads = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": [{"username": row[0], "read_at": row[1]} for row in reads]
        }), 200
    except Exception as e:
        logging.error("공지사항 읽음 목록 조회 오류", exc_info=True)
        return jsonify({"success": False, "message": "공지사항 읽음 목록 조회 실패"}), 500