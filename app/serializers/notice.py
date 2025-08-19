from typing import Dict, List

from .base import Serializer
from app.schemas import (
    notice_schema,
    notices_schema,
    notice_read_schema,
    notice_reads_schema,
    notice_create_schema,
    notice_update_schema,
    notice_read_create_schema,
    notice_delete_schema,
)
from app.models.models import Notice, NoticeRead


class NoticeSerializer:
    """공지사항 관련 직렬화 함수들"""

    @staticmethod
    def serialize_notice(notice) -> Dict:
        """단일 공지사항 직렬화"""
        return Serializer.serialize(notice, notice_schema)

    @staticmethod
    def serialize_notices(notices: List) -> List[Dict]:
        """여러 공지사항 직렬화"""
        return Serializer.serialize(notices, notices_schema, many=True)

    @staticmethod
    def serialize_notice_read(read) -> Dict:
        """단일 공지사항 읽음 정보 직렬화"""
        return Serializer.serialize(read, notice_read_schema)

    @staticmethod
    def serialize_notice_reads(reads: List) -> List[Dict]:
        """여러 공지사항 읽음 정보 직렬화"""
        return Serializer.serialize(reads, notice_reads_schema, many=True)

    @staticmethod
    def deserialize_notice_create(data: Dict) -> Dict:
        """공지사항 생성 데이터 역직렬화"""
        return Serializer.deserialize(data, notice_create_schema)

    @staticmethod
    def deserialize_notice_update(data: Dict) -> Dict:
        """공지사항 수정 데이터 역직렬화"""
        return Serializer.deserialize(data, notice_update_schema, partial=True)

    @staticmethod
    def deserialize_notice_read_create(data: Dict) -> Dict:
        """공지사항 읽음 처리 데이터 역직렬화"""
        return Serializer.deserialize(data, notice_read_create_schema)

    @staticmethod
    def deserialize_notice_delete(data: Dict) -> Dict:
        """공지사항 삭제 데이터 역직렬화"""
        return Serializer.deserialize(data, notice_delete_schema)

    @staticmethod
    def add_notice(session, data: Dict) -> Dict:
        """공지사항 추가"""
        # 데이터 검증
        validated_data = NoticeSerializer.deserialize_notice_create(data)

        # 허용된 사용자 확인
        allowed_users = ["김은지", "장지연", "김슬기"]
        if validated_data.get("created_by") not in allowed_users:
            raise ValueError("공지사항 작성 권한이 없습니다.")

        # 공지사항 생성
        notice = Notice(
            title=validated_data["title"],
            content=validated_data["content"],
            type=validated_data.get("type", "공지사항"),
            created_by=validated_data.get("created_by"),
        )

        session.add(notice)
        session.flush()  # ID를 얻기 위해 flush

        # 저장된 공지사항 직렬화
        serialized_notice = NoticeSerializer.serialize_notice(notice)

        return {"id": notice.id, **serialized_notice}

    @staticmethod
    def get_notices(session) -> List[Dict]:
        """공지사항 조회"""
        # ORM을 사용하여 공지사항 조회
        notices_query = (
            session.query(Notice)
            .filter(Notice.is_deleted == False)
            .order_by(Notice.date.desc())
        )
        notices = []

        for notice in notices_query.all():
            notice_dict = {
                "id": notice.id,
                "type": notice.type or "공지사항",
                "title": notice.title,
                "content": notice.content,
                "date": notice.date.strftime("%Y-%m-%d %H:%M:%S"),
                "created_by": notice.created_by,
            }
            notices.append(notice_dict)

        return notices

    @staticmethod
    def update_notice(session, notice_id: int, data: Dict):
        """공지사항 수정"""
        # 데이터 검증
        validated_data = NoticeSerializer.deserialize_notice_update(data)

        # 수정자 정보 추출
        username = validated_data.get("username")

        if not username:
            raise ValueError("수정자 정보가 누락되었습니다.")

        # 공지사항 존재 확인
        notice = session.query(Notice).filter(Notice.id == notice_id).first()

        if not notice:
            raise ValueError("해당 공지사항을 찾을 수 없습니다.")

        # 공지사항 업데이트
        notice.title = validated_data.get("title")
        notice.content = validated_data.get("content")
        notice.type = validated_data.get("type")
        notice.modified_by = username

        # 수정된 공지사항 직렬화
        return NoticeSerializer.serialize_notice(notice)

    @staticmethod
    def delete_notice(session, notice_id: int):
        """공지사항 삭제 (soft delete)"""
        # 공지사항 존재 확인
        notice = session.query(Notice).filter(Notice.id == notice_id).first()

        if not notice:
            raise ValueError("해당 공지사항을 찾을 수 없습니다.")

        # 공지사항 삭제 (soft delete)
        notice.is_deleted = True

        # 삭제된 공지사항 직렬화
        return NoticeSerializer.serialize_notice(notice)

    @staticmethod
    def mark_notice_read(session, data: Dict):
        """공지사항 읽음 표시"""
        # 데이터 검증
        validated_data = NoticeSerializer.deserialize_notice_read_create(data)

        # 공지사항 존재 확인
        notice = (
            session.query(Notice)
            .filter(Notice.id == validated_data["notice_id"])
            .first()
        )
        if not notice:
            raise ValueError("공지사항을 찾을 수 없습니다.")

        # 이미 읽었는지 확인
        existing_read = (
            session.query(NoticeRead)
            .filter(
                NoticeRead.notice_id == validated_data["notice_id"],
                NoticeRead.username == validated_data["username"],
            )
            .first()
        )

        if not existing_read:
            # 읽음 표시 추가
            notice_read = NoticeRead(
                notice_id=validated_data["notice_id"],
                username=validated_data["username"],
            )
            session.add(notice_read)
            session.flush()  # ID를 얻기 위해 flush
        else:
            notice_read = existing_read

        # 읽음 표시 직렬화
        return NoticeSerializer.serialize_notice_read(notice_read)

    @staticmethod
    def get_notice_reads(session, notice_id: str) -> List[Dict]:
        """공지사항별 읽은 사용자 목록 조회"""
        if not notice_id:
            raise ValueError("공지사항 ID가 필요합니다.")

        # 공지사항 읽음 기록 조회
        reads_query = (
            session.query(NoticeRead)
            .filter(NoticeRead.notice_id == notice_id)
            .order_by(NoticeRead.read_at.desc())
        )

        reads_data = []
        for notice_read in reads_query.all():
            reads_data.append(
                {
                    "username": notice_read.username,
                    "read_at": notice_read.read_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

        return reads_data
