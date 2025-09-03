from datetime import datetime
from marshmallow import Schema, fields, validates, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.models import Issue, IssueComment


# ============================================================================
# Issue 관련 스키마
# ============================================================================


class IssueCommentSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = IssueComment
        load_instance = True
        include_fk = True

    created_at = fields.DateTime(dump_only=True)

    @validates("comment")
    def validate_comment(self, value):
        if not value.strip():
            raise ValidationError("댓글 내용을 입력해주세요.")


class IssueSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Issue
        load_instance = True
        include_fk = True

    created_at = fields.DateTime(dump_only=True)
    comments = fields.Nested(IssueCommentSchema, many=True, dump_only=True)

    @validates("content")
    def validate_content(self, value):
        if not value.strip():
            raise ValidationError("이슈 내용을 입력해주세요.")

    @validates("date")
    def validate_date(self, value):
        if value and value > datetime.now().date():
            raise ValidationError("미래 날짜는 입력할 수 없습니다.")


class IssueCreateSchema(Schema):
    """이슈 생성용 스키마"""

    issue = fields.Str(required=True)  # content → issue로 변경
    training_course = fields.Str()
    username = fields.Str()
    date = fields.Str(allow_none=True)  # Date → Str로 변경, null 허용


class IssueCommentCreateSchema(Schema):
    """이슈 댓글 생성용 스키마"""

    issue_id = fields.Int(required=True)  # nullable=False
    comment = fields.Str(required=True)  # nullable=False
    created_by = fields.Str()


class IssueResolveSchema(Schema):
    """이슈 해결용 스키마"""

    issue_id = fields.Int(required=True)


class IssueCommentFilterSchema(Schema):
    """이슈 댓글 조회 필터 검증용 스키마"""

    issue_id = fields.Int(
        required=True,
        validate=lambda x: x > 0
    )


# ============================================================================
# 스키마 인스턴스 생성
# ============================================================================

issue_schema = IssueSchema()
issues_schema = IssueSchema(many=True)
issue_comment_schema = IssueCommentSchema()
issue_comments_schema = IssueCommentSchema(many=True)
issue_create_schema = IssueCreateSchema()
issue_comment_create_schema = IssueCommentCreateSchema()
issue_resolve_schema = IssueResolveSchema()
issue_comment_filter_schema = IssueCommentFilterSchema()
