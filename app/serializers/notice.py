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
    notice_read_filter_schema,
    notice_list_filter_schema,
)


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
    def deserialize_notice_read_get(query_params: Dict) -> Dict:
        """공지사항 읽음 목록 조회 쿼리 파라미터 검증 및 변환"""
        return Serializer.deserialize(query_params, notice_read_filter_schema)

    @staticmethod
    def deserialize_notice_list_get(query_params: Dict) -> Dict:
        """공지사항 목록 조회 쿼리 파라미터 검증 및 변환"""
        return Serializer.deserialize(query_params, notice_list_filter_schema)

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
