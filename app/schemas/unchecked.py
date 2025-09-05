from marshmallow import Schema, fields, validates, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.models import UncheckedComment, UncheckedDescription


# ============================================================================
# Unchecked 관련 스키마
# ============================================================================


class UncheckedCommentSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UncheckedComment
        load_instance = True
        include_fk = True

    created_at = fields.DateTime(dump_only=True)

    @validates("comment")
    def validate_comment(self, value):
        if not value.strip():
            raise ValidationError("댓글 내용을 입력해주세요.")


class UncheckedDescriptionSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UncheckedDescription
        load_instance = True
        include_fk = True

    created_at = fields.DateTime(dump_only=True)
    comments = fields.Nested(UncheckedCommentSchema, many=True, dump_only=True)

    @validates("content")
    def validate_content(self, value):
        if not value.strip():
            raise ValidationError("미해결 항목 내용을 입력해주세요.")


class UncheckedDescriptionCreateSchema(Schema):
    """미해결 항목 생성용 스키마"""

    description = fields.Str(required=True)  # content → description으로 변경
    training_course = fields.Str()
    user_id = fields.Int()
    username = fields.Str()
    action_plan = fields.Str()
    task_id = fields.Int()
    created_by = fields.Str()

    @validates("description")
    def validate_description(self, value):
        if not value.strip():
            raise ValidationError("미해결 항목 내용을 입력해주세요.")

    @validates("action_plan")
    def validate_action_plan(self, value):
        if value and not value.strip():
            raise ValidationError("액션 플랜을 입력해주세요.")

    @validates("training_course")
    def validate_training_course(self, value):
        if value and not value.strip():
            raise ValidationError("훈련 과정명을 입력해주세요.")


class UncheckedCommentCreateSchema(Schema):
    """미해결 댓글 생성용 스키마"""

    unchecked_id = fields.Int(required=True)  # nullable=False
    comment = fields.Str(required=True)  # nullable=False
    user_id = fields.Int()
    username = fields.Str()
    created_by = fields.Str()

    @validates("comment")
    def validate_comment(self, value):
        if not value.strip():
            raise ValidationError("댓글 내용을 입력해주세요.")


class UncheckedResolveSchema(Schema):
    """미해결 항목 해결용 스키마"""

    unchecked_id = fields.Int(required=True)

    @validates("unchecked_id")
    def validate_unchecked_id(self, value):
        if value <= 0:
            raise ValidationError("유효한 미해결 항목 ID를 입력해주세요.")


class UncheckedCommentFilterSchema(Schema):
    """미해결 댓글 조회 필터 검증용 스키마"""

    unchecked_id = fields.Int(
        required=True,
        validate=lambda x: x > 0
    )


# ============================================================================
# 스키마 인스턴스 생성
# ============================================================================

unchecked_description_schema = UncheckedDescriptionSchema()
unchecked_descriptions_schema = UncheckedDescriptionSchema(many=True)
unchecked_comment_schema = UncheckedCommentSchema()
unchecked_comments_schema = UncheckedCommentSchema(many=True)
unchecked_description_create_schema = UncheckedDescriptionCreateSchema()
unchecked_comment_create_schema = UncheckedCommentCreateSchema()
unchecked_resolve_schema = UncheckedResolveSchema()
unchecked_comment_filter_schema = UncheckedCommentFilterSchema()
