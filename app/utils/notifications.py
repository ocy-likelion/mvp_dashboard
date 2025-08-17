import requests
import logging
from typing import Dict
from decouple import config


class SlackNotifier:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.webhooks: Dict[str, str] = {
            "notice": config("SLACK_WEBHOOK_URL", default=None),  # 공지사항용 웹훅 추가
            "issue": config(
                "SLACK_WEBHOOK_URL_ISSUE", default=None
            ),  # 이슈 등록용 웹훅
            "comment": config("SLACK_WEBHOOK_URL_COMMENT", default=None),  # 댓글용 웹훅
            "default": config(
                "SLACK_WEBHOOK_URL", default=None
            ),  # 기본 웹훅 (기존 URL)
        }
        self.channels: Dict[str, str] = {
            "notice": config("SLACK_CHANNEL", default="C07GLQNQZA5"),  # 공지사항용 채널
            "issue": config(
                "SLACK_ISSUE_CHANNEL", default="C07GLQNQZA5"
            ),  # 이슈용 채널
            "comment": config(
                "SLACK_COMMENT_CHANNEL", default="C07GLQNQZA5"
            ),  # 댓글용 채널
        }

        # 초기화 시 환경 변수 확인
        for channel, url in self.webhooks.items():
            if not url:
                print(f"ERROR: {channel}용 SLACK_WEBHOOK_URL이 설정되지 않았습니다!")
        for channel, id in self.channels.items():
            if not id:
                print(f"ERROR: {channel}용 SLACK_CHANNEL이 설정되지 않았습니다!")

        self.logger.info(f"SlackNotifier 초기화: channels={self.channels}")

    def send_notification(self, message: str, channel_type: str = "default") -> bool:
        webhook_url = self.webhooks.get(channel_type)
        channel_id = self.channels.get(
            channel_type, self.channels["notice"]
        )  # 기본값은 공지사항 채널

        if not webhook_url:
            logging.error(
                f"ERROR: {channel_type}용 SLACK_WEBHOOK_URL이 설정되지 않았습니다!"
            )
            return False

        try:
            payload = {"text": message, "channel": channel_id}

            response = requests.post(webhook_url, json={"text": message})
            if response.status_code == 200:
                logging.info(
                    f"Slack 알림 전송 성공 (채널: {channel_type}, 채널ID: {channel_id})"
                )
                return True
            else:
                logging.error(
                    f"Slack 알림 전송 실패 (채널: {channel_type}, 채널ID: {channel_id}): {response.status_code}"
                )
                return False
        except Exception as e:
            logging.error(
                f"Slack 알림 전송 중 오류 발생 (채널: {channel_type}, 채널ID: {channel_id}): {str(e)}"
            )
            return False

    def notify_new_notice(self, title, author):
        message = f"""
📢 *새로운 공지사항이 등록되었습니다!* 확인 후 체크이모지*✅를 반드시 눌러주세요!
• 작성자: {author}
• 제목: {title}
"""
        return self.send_notification(message, "default")

    def notify_new_issue(self, issue, author, training_course):
        message = f"""
⚠️ *새로운 이슈가 등록되었습니다!*
• 교육과정: {training_course}
• 작성자: {author}
• 내용: {issue}
"""
        return self.send_notification(message, "issue")

    def notify_new_comment(self, issue_title, author, training_course):
        message = f"""
💬 *새로운 댓글이 등록되었습니다!*
• 교육과정: {training_course}
• 이슈: {issue_title}
• 작성자: {author}
"""
        return self.send_notification(message, "comment")
