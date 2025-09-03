from datetime import datetime
from marshmallow import Schema, fields, validates, ValidationError


# ============================================================================
# 응답 래퍼 스키마
# ============================================================================


class PaginationSchema(Schema):
    """페이지네이션 정보 스키마"""

    page = fields.Int(description="현재 페이지 번호")
    per_page = fields.Int(description="페이지당 항목 수")
    total_count = fields.Int(description="전체 항목 수")
    total_pages = fields.Int(description="전체 페이지 수")
    has_prev = fields.Bool(description="이전 페이지 존재 여부")
    has_next = fields.Bool(description="다음 페이지 존재 여부")


class ResponseSchema(Schema):
    """API 응답 래퍼 스키마"""

    success = fields.Bool(description="요청 성공 여부")
    message = fields.Str(description="응답 메시지")
    data = fields.Raw(description="응답 데이터")
    status_code = fields.Int(description="HTTP 상태 코드")


class PaginatedResponseSchema(Schema):
    """페이지네이션 응답 스키마"""

    success = fields.Bool(description="요청 성공 여부")
    message = fields.Str(description="응답 메시지")
    data = fields.Dict(description="페이지네이션 데이터", keys=fields.Str(), values=fields.Raw())
    status_code = fields.Int(description="HTTP 상태 코드")


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


class CombinedTaskStatusResponseSchema(Schema):
    """통합 업무 상태 응답용 스키마"""

    training_course = fields.Str(required=True, description="훈련 과정명")
    dept = fields.Str(required=True, description="부서명")
    manager_name = fields.Str(required=True, description="담당자명")
    daily_check_rate = fields.Str(required=True, description="당일 체크율")
    yesterday_check_rate = fields.Str(required=True, description="전날 체크율")
    overall_check_rate = fields.Str(required=True, description="전체 체크율")


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
paginated_response_schema = PaginatedResponseSchema()
error_schema = ErrorSchema()
pagination_schema = PaginationSchema()
date_filter_schema = DateFilterSchema()
task_status_response_schema = TaskStatusResponseSchema()
combined_task_status_response_schema = CombinedTaskStatusResponseSchema()
notification_query_schema = NotificationQuerySchema()
