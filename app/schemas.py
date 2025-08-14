from datetime import datetime
from marshmallow import Schema, fields, post_load, validates, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, auto_field
from app.models.models import (
    User,
    Attendance,
    Issue,
    IssueComment,
    Notice,
    NoticeRead,
    TaskItem,
    TaskChecklist,
    UncheckedComment,
    UncheckedDescription,
    TrainingInfo,
    UserLastCheck,
)


# ============================================================================
# User 관련 스키마
# ============================================================================


class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        include_fk = True

    # 민감한 정보는 직렬화에서 제외
    password = fields.Str(load_only=True)  # 역직렬화만 가능
    created_at = fields.DateTime(dump_only=True)  # 직렬화만 가능
    last_login = fields.DateTime(dump_only=True)

    @validates("email")
    def validate_email(self, value):
        if "@" not in value:
            raise ValidationError("유효한 이메일 주소를 입력해주세요.")

    @validates("username")
    def validate_username(self, value):
        if len(value) < 3:
            raise ValidationError("사용자명은 최소 3자 이상이어야 합니다.")


class UserCreateSchema(Schema):
    """사용자 생성용 스키마"""

    username = fields.Str(required=True, validate=lambda x: len(x) >= 3)
    password = fields.Str(required=True, validate=lambda x: len(x) >= 6)
    name = fields.Str(required=True)
    email = fields.Email(required=True)


class UserUpdateSchema(Schema):
    """사용자 수정용 스키마"""

    name = fields.Str()
    email = fields.Email()
    is_verified = fields.Bool()


class UserLoginSchema(Schema):
    """로그인용 스키마"""

    username = fields.Str(required=True)
    password = fields.Str(required=True)


# ============================================================================
# Attendance 관련 스키마
# ============================================================================


class AttendanceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Attendance
        load_instance = True
        include_fk = True

    date = fields.Date(required=True)  # nullable=False
    check_in_time = fields.Time()
    check_out_time = fields.Time()

    @validates("date")
    def validate_date(self, value):
        if value > datetime.now().date():
            raise ValidationError("미래 날짜는 입력할 수 없습니다.")


class AttendanceCreateSchema(Schema):
    """출석 생성용 스키마"""

    date = fields.Date(required=True)
    instructor = fields.Str()
    instructor_name = fields.Str()
    training_course = fields.Str()
    check_in_time = fields.Time()
    check_out_time = fields.Time()
    daily_log = fields.Bool()


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

    content = fields.Str(required=True)  # nullable=False
    training_course = fields.Str()
    username = fields.Str()
    created_by = fields.Str()
    date = fields.Date()


class IssueCommentCreateSchema(Schema):
    """이슈 댓글 생성용 스키마"""

    issue_id = fields.Int(required=True)  # nullable=False
    comment = fields.Str(required=True)  # nullable=False
    created_by = fields.Str()


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

    date = fields.DateTime(dump_only=True)
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


# ============================================================================
# Task 관련 스키마
# ============================================================================


class TaskChecklistSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = TaskChecklist
        load_instance = True
        include_fk = True

    checked_date = fields.DateTime(dump_only=True)


class TaskItemSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = TaskItem
        load_instance = True
        include_fk = True

    checklists = fields.Nested(TaskChecklistSchema, many=True, dump_only=True)
    unchecked_descriptions = fields.Nested(
        "UncheckedDescriptionSchema", many=True, dump_only=True
    )

    @validates("task_name")
    def validate_task_name(self, value):
        if not value.strip():
            raise ValidationError("작업명을 입력해주세요.")


class TaskItemCreateSchema(Schema):
    """작업 항목 생성용 스키마"""

    task_name = fields.Str(required=True)  # nullable=False
    task_period = fields.Str()
    task_category = fields.Str()
    guide = fields.Str()
    due = fields.Int()


class TaskChecklistCreateSchema(Schema):
    """작업 체크리스트 생성용 스키마"""

    task_id = fields.Int(required=True)  # nullable=False
    training_course = fields.Str(required=True)  # nullable=False
    username = fields.Str(required=True)  # nullable=False
    user_id = fields.Int()


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

    content = fields.Str(required=True)  # nullable=False
    training_course = fields.Str()
    user_id = fields.Int()
    username = fields.Str()
    action_plan = fields.Str()
    task_id = fields.Int()
    created_by = fields.Str()


class UncheckedCommentCreateSchema(Schema):
    """미해결 댓글 생성용 스키마"""

    unchecked_id = fields.Int(required=True)  # nullable=False
    comment = fields.Str(required=True)  # nullable=False
    user_id = fields.Int()
    username = fields.Str()
    created_by = fields.Str()


# ============================================================================
# Training 관련 스키마
# ============================================================================


class TrainingInfoSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = TrainingInfo
        load_instance = True
        include_fk = True

    created_at = fields.DateTime(dump_only=True)

    @validates("training_course")
    def validate_training_course(self, value):
        if not value.strip():
            raise ValidationError("교육 과정명을 입력해주세요.")


class TrainingInfoCreateSchema(Schema):
    """교육 정보 생성용 스키마"""

    training_course = fields.Str(required=True)  # nullable=False
    start_date = fields.Date()
    end_date = fields.Date()
    dept = fields.Str()
    manager_name = fields.Str()


class TrainingInfoUpdateSchema(Schema):
    """교육 정보 수정용 스키마"""

    training_course = fields.Str()
    start_date = fields.Date()
    end_date = fields.Date()
    dept = fields.Str()
    manager_name = fields.Str()


# ============================================================================
# UserLastCheck 관련 스키마
# ============================================================================


class UserLastCheckSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UserLastCheck
        load_instance = True
        include_fk = True


class UserLastCheckUpdateSchema(Schema):
    """사용자 마지막 확인 시간 업데이트용 스키마"""

    username = fields.Str(required=True)  # nullable=False
    last_notice_check = fields.DateTime()
    last_issue_check = fields.DateTime()
    last_comment_check = fields.DateTime()


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
# 스키마 인스턴스 생성
# ============================================================================

# 단일 객체용 스키마
user_schema = UserSchema()
attendance_schema = AttendanceSchema()
issue_schema = IssueSchema()
issue_comment_schema = IssueCommentSchema()
notice_schema = NoticeSchema()
notice_read_schema = NoticeReadSchema()
task_item_schema = TaskItemSchema()
task_checklist_schema = TaskChecklistSchema()
unchecked_description_schema = UncheckedDescriptionSchema()
unchecked_comment_schema = UncheckedCommentSchema()
training_info_schema = TrainingInfoSchema()
user_last_check_schema = UserLastCheckSchema()

# 다중 객체용 스키마
users_schema = UserSchema(many=True)
attendances_schema = AttendanceSchema(many=True)
issues_schema = IssueSchema(many=True)
issue_comments_schema = IssueCommentSchema(many=True)
notices_schema = NoticeSchema(many=True)
notice_reads_schema = NoticeReadSchema(many=True)
task_items_schema = TaskItemSchema(many=True)
task_checklists_schema = TaskChecklistSchema(many=True)
unchecked_descriptions_schema = UncheckedDescriptionSchema(many=True)
unchecked_comments_schema = UncheckedCommentSchema(many=True)
training_infos_schema = TrainingInfoSchema(many=True)
user_last_checks_schema = UserLastCheckSchema(many=True)

# 생성/수정용 스키마
user_create_schema = UserCreateSchema()
user_update_schema = UserUpdateSchema()
user_login_schema = UserLoginSchema()
attendance_create_schema = AttendanceCreateSchema()
issue_create_schema = IssueCreateSchema()
issue_comment_create_schema = IssueCommentCreateSchema()
notice_create_schema = NoticeCreateSchema()
notice_update_schema = NoticeUpdateSchema()
task_item_create_schema = TaskItemCreateSchema()
task_checklist_create_schema = TaskChecklistCreateSchema()
unchecked_description_create_schema = UncheckedDescriptionCreateSchema()
unchecked_comment_create_schema = UncheckedCommentCreateSchema()
training_info_create_schema = TrainingInfoCreateSchema()
training_info_update_schema = TrainingInfoUpdateSchema()
user_last_check_update_schema = UserLastCheckUpdateSchema()

# 응답 래퍼 스키마
response_schema = ResponseSchema()
error_schema = ErrorSchema()
pagination_schema = PaginationSchema()
