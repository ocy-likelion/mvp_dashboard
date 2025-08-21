from datetime import datetime
from marshmallow import Schema, fields, validates, ValidationError


# ============================================================================
# 응답 래퍼 스키마
# ============================================================================


class PaginationSchema(Schema):
    """페이지네이션 정보 스키마"""

    page = fields.Int()
    per_page = fields.Int()
    total = fields.Int()
    pages = fields.Int()
    has_prev = fields.Bool()
    has_next = fields.Bool()


class ResponseSchema(Schema):
    """API 응답 래퍼 스키마"""

    success = fields.Bool()
    message = fields.Str()
    data = fields.Raw()
    pagination = fields.Nested(PaginationSchema)


class ErrorSchema(Schema):
    """에러 응답 스키마"""

    success = fields.Bool()
    error = fields.Str()
    details = fields.Raw()


# ============================================================================
# Admin 관련 공통 스키마
# ============================================================================


class DateFilterSchema(Schema):
    """날짜 필터 검증용 스키마"""

    date = fields.Date(
        required=False,
        allow_none=False,
        format="%Y-%m-%d",
        load_default=lambda: datetime.now().date(),
        dump_default=lambda: datetime.now().date(),
    )


class TaskStatusResponseSchema(Schema):
    """업무 상태 응답용 스키마"""

    task_status = fields.List(fields.Dict(), required=True)
    total_courses = fields.Int(required=True)
    timestamp = fields.DateTime(required=True, format="iso")


# ============================================================================
# Notification 관련 스키마
# ============================================================================


class NotificationQuerySchema(Schema):
    """알림 조회용 스키마"""

    username = fields.Str(required=True)

    @validates("username")
    def validate_username(self, value):
        if not value.strip():
            raise ValidationError("사용자명을 입력해주세요.")


# ============================================================================
# 스키마 인스턴스 생성
# ============================================================================

response_schema = ResponseSchema()
error_schema = ErrorSchema()
pagination_schema = PaginationSchema()
date_filter_schema = DateFilterSchema()
task_status_response_schema = TaskStatusResponseSchema()
notification_query_schema = NotificationQuerySchema()
