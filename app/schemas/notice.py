from marshmallow import Schema, fields, validates, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.models import Notice, NoticeRead


# ============================================================================
# Notice 관련 스키마
# ============================================================================


class NoticeReadSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = NoticeRead
        load_instance = True
        include_fk = True

    read_at = fields.DateTime(dump_only=True)
    notice_id = fields.Int(required=True)  # nullable=False
    username = fields.Str(required=True)  # nullable=False


class NoticeSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Notice
        load_instance = True
        include_fk = True

    date = fields.Str(dump_only=True)  # 문자열로 변경
    reads = fields.Nested(NoticeReadSchema, many=True, dump_only=True)

    @validates("title")
    def validate_title(self, value):
        if not value.strip():
            raise ValidationError("공지사항 제목을 입력해주세요.")

    @validates("content")
    def validate_content(self, value):
        if not value.strip():
            raise ValidationError("공지사항 내용을 입력해주세요.")


class NoticeCreateSchema(Schema):
    """공지사항 생성용 스키마"""

    type = fields.Str()
    title = fields.Str(required=True)  # nullable=False
    content = fields.Str(required=True)  # nullable=False
    created_by = fields.Str()


class NoticeUpdateSchema(Schema):
    """공지사항 수정용 스키마"""

    type = fields.Str()
    title = fields.Str()
    content = fields.Str()
    modified_by = fields.Str()


class NoticeReadCreateSchema(Schema):
    """공지사항 읽음 처리용 스키마"""

    notice_id = fields.Int(required=True)
    username = fields.Str(required=True)


class NoticeDeleteSchema(Schema):
    """공지사항 삭제용 스키마"""

    notice_id = fields.Int(required=True)
    username = fields.Str(required=True)

    @validates("username")
    def validate_username(self, value):
        allowed_users = ["김은지", "장지연", "김슬기"]
        if value not in allowed_users:
            raise ValidationError("공지사항 삭제 권한이 없습니다.")


class NoticeReadFilterSchema(Schema):
    """공지사항 읽음 목록 조회 필터 검증용 스키마"""

    notice_id = fields.Int(
        required=True,
        validate=lambda x: x > 0
    )


class NoticeListFilterSchema(Schema):
    """공지사항 목록 조회 필터 검증용 스키마"""

    page = fields.Int(missing=1, validate=lambda x: x > 0)
    per_page = fields.Int(missing=10, validate=lambda x: 1 <= x <= 100)
    type = fields.Str()
    search = fields.Str()


# ============================================================================
# 스키마 인스턴스 생성
# ============================================================================

notice_schema = NoticeSchema()
notices_schema = NoticeSchema(many=True)
notice_read_schema = NoticeReadSchema()
notice_reads_schema = NoticeReadSchema(many=True)
notice_create_schema = NoticeCreateSchema()
notice_update_schema = NoticeUpdateSchema()
notice_read_create_schema = NoticeReadCreateSchema()
notice_delete_schema = NoticeDeleteSchema()
notice_read_filter_schema = NoticeReadFilterSchema()
notice_list_filter_schema = NoticeListFilterSchema()
