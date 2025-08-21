"""
Notice service for notice-related business logic
"""

from typing import Dict, List

from app.utils.database import db_session, db_session_read_only
from .base_service import BaseService
from app.models.models import Notice, NoticeRead


class NoticeService(BaseService):
    """공지사항 관련 비즈니스 로직 처리"""

    # 공지사항 작성 권한이 있는 사용자 목록
    ALLOWED_USERS = ["김은지", "장지연", "김슬기"]

    @staticmethod
    def create_notice(notice_data: Dict) -> Notice:
        """공지사항 추가"""
        # 허용된 사용자 확인
        created_by = notice_data.get("created_by")
        if created_by not in NoticeService.ALLOWED_USERS:
            raise ValueError("공지사항 작성 권한이 없습니다.")

        with db_session() as session:
            # 공지사항 생성
            notice = Notice(
                title=notice_data["title"],
                content=notice_data["content"],
                type=notice_data.get("type", "공지사항"),
                created_by=created_by,
            )

            NoticeService.flush_and_get_id(session, notice)
            return notice

    @staticmethod
    def get_notices(include_deleted: bool = False) -> List[Dict]:
        """공지사항 조회"""
        with db_session_read_only() as session:
            # 기본적으로 삭제되지 않은 공지사항만 조회
            query = session.query(Notice)
            if not include_deleted:
                query = query.filter(Notice.is_deleted == False)

            notices = query.order_by(Notice.date.desc()).all()

            notices_data = []
            for notice in notices:
                notice_dict = {
                    "id": notice.id,
                    "type": notice.type or "공지사항",
                    "title": notice.title,
                    "content": notice.content,
                    "date": notice.date.strftime("%Y-%m-%d %H:%M:%S"),
                    "created_by": notice.created_by,
                    "modified_by": notice.modified_by,
                    "is_deleted": notice.is_deleted,
                }
                notices_data.append(notice_dict)

            return notices_data

    @staticmethod
    def update_notice(notice_id: int, validated_data: Dict) -> Notice:
        """공지사항 수정"""
        username = validated_data["username"]

        with db_session() as session:
            # 공지사항 존재 확인
            notice = NoticeService.safe_get_by_id(
                session, Notice, notice_id, "해당 공지사항을 찾을 수 없습니다."
            )

            # 삭제된 공지사항은 수정 불가
            if notice.is_deleted:
                raise ValueError("삭제된 공지사항은 수정할 수 없습니다.")

            # 공지사항 업데이트
            if "title" in validated_data:
                notice.title = validated_data["title"]
            if "content" in validated_data:
                notice.content = validated_data["content"]
            if "type" in validated_data:
                notice.type = validated_data["type"]

            notice.modified_by = username

            return notice

    @staticmethod
    def delete_notice(notice_id: int) -> Notice:
        """공지사항 삭제 (soft delete)"""
        with db_session() as session:
            # 공지사항 존재 확인
            notice = NoticeService.safe_get_by_id(
                session, Notice, notice_id, "해당 공지사항을 찾을 수 없습니다."
            )

            # 이미 삭제된 공지사항 확인
            if notice.is_deleted:
                raise ValueError("이미 삭제된 공지사항입니다.")

            # 공지사항 삭제 (soft delete)
            notice.is_deleted = True

            return notice

    @staticmethod
    def mark_notice_read(validated_data: Dict) -> NoticeRead:
        """공지사항 읽음 표시"""
        notice_id = validated_data["notice_id"]
        username = validated_data["username"]

        with db_session() as session:
            # 공지사항 존재 확인
            notice = NoticeService.safe_get_by_id(
                session, Notice, notice_id, "공지사항을 찾을 수 없습니다."
            )

            # 삭제된 공지사항은 읽음 처리 불가
            if notice.is_deleted:
                raise ValueError("삭제된 공지사항은 읽음 처리할 수 없습니다.")

            # 이미 읽었는지 확인
            existing_read = (
                session.query(NoticeRead)
                .filter(
                    NoticeRead.notice_id == notice_id,
                    NoticeRead.username == username,
                )
                .first()
            )

            if existing_read:
                return existing_read

            # 읽음 표시 추가
            notice_read = NoticeRead(
                notice_id=notice_id,
                username=username,
            )

            NoticeService.flush_and_get_id(session, notice_read)
            return notice_read

    @staticmethod
    def get_notice_reads(notice_id: int) -> List[Dict]:
        """공지사항별 읽은 사용자 목록 조회"""
        with db_session_read_only() as session:
            # 공지사항 존재 확인
            NoticeService.safe_get_by_id(
                session, Notice, notice_id, "공지사항을 찾을 수 없습니다."
            )

            # 공지사항 읽음 기록 조회
            reads = (
                session.query(NoticeRead)
                .filter(NoticeRead.notice_id == notice_id)
                .order_by(NoticeRead.read_at.desc())
                .all()
            )

            reads_data = []
            for notice_read in reads:
                reads_data.append(
                    {
                        "id": notice_read.id,
                        "username": notice_read.username,
                        "read_at": notice_read.read_at.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )

            return reads_data

    @staticmethod
    def get_notice_by_id(notice_id: int, include_deleted: bool = False) -> Notice:
        """ID로 공지사항 조회"""
        with db_session_read_only() as session:
            notice = NoticeService.safe_get_by_id(
                session, Notice, notice_id, "공지사항을 찾을 수 없습니다."
            )

            if not include_deleted and notice.is_deleted:
                raise ValueError("삭제된 공지사항입니다.")

            return notice

    @staticmethod
    def get_unread_notices_for_user(username: str) -> List[Notice]:
        """사용자가 읽지 않은 공지사항 목록 조회"""
        with db_session_read_only() as session:
            # 사용자가 읽은 공지사항 ID 목록
            read_notice_ids = (
                session.query(NoticeRead.notice_id)
                .filter(NoticeRead.username == username)
                .all()
            )
            read_ids = [notice_id[0] for notice_id in read_notice_ids]

            # 읽지 않은 공지사항 조회
            unread_notices = (
                session.query(Notice)
                .filter(
                    Notice.is_deleted == False,
                    ~Notice.id.in_(read_ids) if read_ids else True,
                )
                .order_by(Notice.date.desc())
                .all()
            )

            return unread_notices

    @staticmethod
    def check_write_permission(username: str) -> bool:
        """공지사항 작성 권한 확인"""
        return username in NoticeService.ALLOWED_USERS

    @staticmethod
    def restore_notice(notice_id: int) -> Notice:
        """삭제된 공지사항 복원"""
        with db_session() as session:
            notice = NoticeService.safe_get_by_id(
                session, Notice, notice_id, "공지사항을 찾을 수 없습니다."
            )

            if not notice.is_deleted:
                raise ValueError("삭제되지 않은 공지사항입니다.")

            notice.is_deleted = False
            return notice
