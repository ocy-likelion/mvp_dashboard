from typing import Any, Dict, List, Optional
from marshmallow import ValidationError, Schema
from flask import jsonify

# 모든 스키마 imports
from app.schemas import (
    # 단일 객체 스키마
    user_schema,
    attendance_schema,
    issue_schema,
    issue_comment_schema,
    notice_schema,
    notice_read_schema,
    task_item_schema,
    task_checklist_schema,
    unchecked_description_schema,
    unchecked_comment_schema,
    training_info_schema,
    # 다중 객체 스키마
    users_schema,
    attendances_schema,
    issues_schema,
    issue_comments_schema,
    notices_schema,
    notice_reads_schema,
    task_items_schema,
    task_checklists_schema,
    unchecked_descriptions_schema,
    unchecked_comments_schema,
    training_infos_schema,
    # 생성/수정 스키마
    user_create_schema,
    user_update_schema,
    user_login_schema,
    password_change_schema,
    attendance_create_schema,
    issue_create_schema,
    issue_comment_create_schema,
    notice_create_schema,
    notice_update_schema,
    task_item_create_schema,
    task_checklist_create_schema,
    unchecked_description_create_schema,
    unchecked_comment_create_schema,
    training_info_create_schema,
    training_info_update_schema,
    # 추가 검증용 스키마
    task_update_schema,
    irregular_task_create_schema,
    unchecked_resolve_schema,
    notice_read_create_schema,
    notice_delete_schema,
    issue_resolve_schema,
    notification_query_schema,
    # 응답 스키마
    response_schema,
    error_schema,
    pagination_schema,
)


class Serializer:
    """Marshmallow 스키마를 사용한 직렬화/역직렬화 처리 클래스"""

    @staticmethod
    def serialize(obj: Any, schema: Schema, many: bool = False) -> Dict:
        """
        객체를 직렬화하여 딕셔너리로 반환

        Args:
            obj: 직렬화할 객체 또는 객체 리스트
            schema: 사용할 Marshmallow 스키마
            many: 여러 객체를 직렬화할지 여부

        Returns:
            직렬화된 딕셔너리
        """
        try:
            if many:
                return schema.dump(obj, many=True)
            else:
                return schema.dump(obj)
        except Exception as e:
            raise ValidationError(f"직렬화 중 오류가 발생했습니다: {str(e)}")

    @staticmethod
    def deserialize(data: Dict, schema: Schema, partial: bool = False) -> Dict:
        """
        딕셔너리를 역직렬화하여 검증된 데이터로 반환

        Args:
            data: 역직렬화할 딕셔너리
            schema: 사용할 Marshmallow 스키마
            partial: 부분 업데이트 허용 여부

        Returns:
            검증된 딕셔너리
        """
        try:
            return schema.load(data, partial=partial)
        except ValidationError as e:
            raise ValidationError(f"데이터 검증 실패: {e.messages}")

    @staticmethod
    def validate(data: Dict, schema: Schema) -> Dict:
        """
        데이터 검증만 수행 (역직렬화하지 않음)

        Args:
            data: 검증할 딕셔너리
            schema: 사용할 Marshmallow 스키마

        Returns:
            검증된 딕셔너리
        """
        try:
            return schema.validate(data)
        except ValidationError as e:
            raise ValidationError(f"데이터 검증 실패: {e.messages}")


class ResponseSerializer:
    """API 응답 직렬화 처리 클래스"""

    @staticmethod
    def success_response(
        data: Any = None, message: str = "성공", pagination: Optional[Dict] = None
    ) -> Dict:
        """
        성공 응답 생성

        Args:
            data: 응답 데이터
            message: 응답 메시지
            pagination: 페이지네이션 정보

        Returns:
            성공 응답 딕셔너리
        """
        response = {"success": True, "message": message, "data": data}

        if pagination:
            response["pagination"] = pagination

        return response

    @staticmethod
    def error_response(
        error: str, details: Optional[Dict] = None, status_code: int = 400
    ) -> Dict:
        """
        에러 응답 생성

        Args:
            error: 에러 메시지
            details: 상세 에러 정보
            status_code: HTTP 상태 코드

        Returns:
            에러 응답 딕셔너리
        """
        return {
            "success": False,
            "error": error,
            "details": details,
            "status_code": status_code,
        }

    @staticmethod
    def pagination_response(
        items: List[Any], page: int, per_page: int, total: int, schema: Schema
    ) -> Dict:
        """
        페이지네이션 응답 생성

        Args:
            items: 아이템 리스트
            page: 현재 페이지
            per_page: 페이지당 아이템 수
            total: 전체 아이템 수
            schema: 직렬화할 스키마

        Returns:
            페이지네이션 응답 딕셔너리
        """
        # 아이템 직렬화
        serialized_items = Serializer.serialize(items, schema, many=True)

        # 페이지네이션 정보 계산
        pages = (total + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < pages

        pagination = {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": pages,
            "has_prev": has_prev,
            "has_next": has_next,
        }

        return ResponseSerializer.success_response(
            data=serialized_items, pagination=pagination
        )
