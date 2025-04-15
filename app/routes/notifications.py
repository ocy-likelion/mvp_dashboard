# app/routes/notifications.py
from flask import Blueprint, request, jsonify
from datetime import datetime
from app.models.db import get_db_connection
from app.utils.notifications import SlackNotifier
import logging
import requests

notifications_bp = Blueprint('notifications', __name__)
slack_notifier = SlackNotifier()

@notifications_bp.route('/notifications/unread-count', methods=['GET'])
def get_unread_count():
    """사용자별 미확인 알림 개수 조회"""
    try:
        username = request.args.get('username')
        if not username:
            return jsonify({"success": False, "message": "사용자명이 필요합니다."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # 사용자의 마지막 확인 시간 조회
        cursor.execute("""
            SELECT last_notice_check, last_issue_check, last_comment_check 
            FROM user_last_checks 
            WHERE username = %s
        """, (username,))
        
        last_check = cursor.fetchone()
        if not last_check:
            # 첫 로그인인 경우 현재 시간으로 초기화
            cursor.execute("""
                INSERT INTO user_last_checks 
                (username, last_notice_check, last_issue_check, last_comment_check)
                VALUES (%s, NOW(), NOW(), NOW())
            """, (username,))
            conn.commit()
            return jsonify({
                "success": True,
                "data": {
                    "new_notices": 0,
                    "new_issues": 0,
                    "new_comments": 0
                }
            }), 200

        # 새로운 항목 개수 조회
        last_notice_check, last_issue_check, last_comment_check = last_check

        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM notices WHERE date > %s) as new_notices,
                (SELECT COUNT(*) FROM issues WHERE created_at > %s) as new_issues,
                (SELECT COUNT(*) FROM issue_comments WHERE created_at > %s) as new_comments
        """, (last_notice_check, last_issue_check, last_comment_check))
        
        counts = cursor.fetchone()
        
        # 현재 시간으로 마지막 확인 시간 업데이트
        cursor.execute("""
            UPDATE user_last_checks 
            SET last_notice_check = NOW(),
                last_issue_check = NOW(),
                last_comment_check = NOW()
            WHERE username = %s
        """, (username,))
        
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": {
                "new_notices": counts[0],
                "new_issues": counts[1],
                "new_comments": counts[2]
            }
        }), 200

    except Exception as e:
        logging.error("알림 개수 조회 오류", exc_info=True)
        return jsonify({"success": False, "message": "알림 개수 조회 실패"}), 500

def send_notification(self, message):
    if not self.webhook_url:
        logging.error("SLACK_WEBHOOK_URL이 설정되지 않았습니다.")
        logging.error(f"현재 환경변수: WEBHOOK_URL={self.webhook_url}, CHANNEL={self.channel}")
        return False
        
    try:
        payload = {
            "channel": self.channel,
            "text": message,
            "username": "Lion Helper Bot",
            "icon_emoji": ":lion_face:"
        }
        
        logging.info(f"Slack webhook 호출 시도 - Channel: {self.channel}")
        response = requests.post(self.webhook_url, json=payload)
        logging.info(f"Slack 응답 코드: {response.status_code}")
        logging.info(f"Slack 응답 내용: {response.text}")
        
        if response.status_code == 200:
            return True
        else:
            logging.error(f"Slack 알림 전송 실패: {response.status_code}, {response.text}")
            return False
    except Exception as e:
        logging.error(f"Slack 알림 전송 중 오류 발생: {str(e)}", exc_info=True)
        return False