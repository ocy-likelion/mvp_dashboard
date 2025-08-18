from datetime import datetime
from marshmallow import Schema, fields, validates, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
import re
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
    password = fields.Str(required=True)
    name = fields.Str(required=True)
    email = fields.Email(required=True)

    @validates("password")
    def validate_password_strength(self, value):
        if len(value) < 8:
            raise ValidationError("비밀번호는 최소 8자 이상이어야 합니다.")

        if not re.search(r"[A-Z]", value):
            raise ValidationError("비밀번호는 대문자를 포함해야 합니다.")

        if not re.search(r"[a-z]", value):
            raise ValidationError("비밀번호는 소문자를 포함해야 합니다.")

        if not re.search(r"\d", value):
            raise ValidationError("비밀번호는 숫자를 포함해야 합니다.")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise ValidationError("비밀번호는 특수문자를 포함해야 합니다.")


class UserUpdateSchema(Schema):
    """사용자 수정용 스키마"""

    name = fields.Str()
    email = fields.Email()
    is_verified = fields.Bool()


class UserLoginSchema(Schema):
    """로그인용 스키마"""

    username = fields.Str(required=True)
    password = fields.Str(required=True)

    @validates("password")
    def validate_password(self, value):
        if not value.strip():
            raise ValidationError("비밀번호를 입력해주세요.")


class PasswordChangeSchema(Schema):
    """비밀번호 변경용 스키마"""

    username = fields.Str(required=True)
    current_password = fields.Str(required=True)
    new_password = fields.Str(required=True)

    @validates("current_password")
    def validate_current_password(self, value):
        if not value.strip():
            raise ValidationError("현재 비밀번호를 입력해주세요.")

    @validates("new_password")
    def validate_new_password_strength(self, value):
        if len(value) < 8:
            raise ValidationError("비밀번호는 최소 8자 이상이어야 합니다.")

        if not re.search(r"[A-Z]", value):
            raise ValidationError("비밀번호는 대문자를 포함해야 합니다.")

        if not re.search(r"[a-z]", value):
            raise ValidationError("비밀번호는 소문자를 포함해야 합니다.")

        if not re.search(r"\d", value):
            raise ValidationError("비밀번호는 숫자를 포함해야 합니다.")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise ValidationError("비밀번호는 특수문자를 포함해야 합니다.")


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


class TaskUpdateSchema(Schema):
    """작업 체크리스트 업데이트용 스키마"""

    updates = fields.List(fields.Dict(), required=True)
    training_course = fields.Str(required=True)
    username = fields.Str(required=True)

    @validates("updates")
    def validate_updates(self, value):
        if not value:
            raise ValidationError("업데이트 데이터가 필요합니다.")
        
        for update in value:
            if "task_name" not in update:
                raise ValidationError("각 업데이트에 task_name이 필요합니다.")
            if "is_checked" not in update:
                raise ValidationError("각 업데이트에 is_checked가 필요합니다.")


class IrregularTaskCreateSchema(Schema):
    """불규칙 업무 생성용 스키마"""

    updates = fields.List(fields.Dict(), required=True)
    training_course = fields.Str(required=True)

    @validates("updates")
    def validate_updates(self, value):
        if not value:
            raise ValidationError("업데이트 데이터가 필요합니다.")
        
        for update in value:
            if "task_name" not in update:
                raise ValidationError("각 업데이트에 task_name이 필요합니다.")
            if "is_checked" not in update:
                raise ValidationError("각 업데이트에 is_checked가 필요합니다.")


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

    @validates("content")
    def validate_content(self, value):
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
    resolved_by = fields.Str(required=True)
    resolution_comment = fields.Str()

    @validates("unchecked_id")
    def validate_unchecked_id(self, value):
        if value <= 0:
            raise ValidationError("유효한 미해결 항목 ID를 입력해주세요.")


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
    start_date = fields.Str(required=True)  # 문자열로 받아서 변환
    end_date = fields.Str(required=True)  # 문자열로 받아서 변환
    dept = fields.Str(required=True)
    manager_name = fields.Str(required=True)

    @validates("start_date")
    def validate_start_date(self, value):
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise ValidationError("시작 날짜는 YYYY-MM-DD 형식이어야 합니다.")

    @validates("end_date")
    def validate_end_date(self, value):
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise ValidationError("종료 날짜는 YYYY-MM-DD 형식이어야 합니다.")


class TrainingInfoUpdateSchema(Schema):
    """교육 정보 수정용 스키마"""

    training_course = fields.Str()
    start_date = fields.Str()
    end_date = fields.Str()
    dept = fields.Str()
    manager_name = fields.Str()

    @validates("start_date")
    def validate_start_date(self, value):
        if value:
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                raise ValidationError("시작 날짜는 YYYY-MM-DD 형식이어야 합니다.")

    @validates("end_date")
    def validate_end_date(self, value):
        if value:
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                raise ValidationError("종료 날짜는 YYYY-MM-DD 형식이어야 합니다.")


# ============================================================================
# Notice 관련 추가 스키마
# ============================================================================


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


# ============================================================================
# Issue 관련 추가 스키마
# ============================================================================


class IssueResolveSchema(Schema):
    """이슈 해결용 스키마"""

    issue_id = fields.Int(required=True)
    resolved_by = fields.Str()
    resolution_comment = fields.Str()

    @validates("issue_id")
    def validate_issue_id(self, value):
        if value <= 0:
            raise ValidationError("유효한 이슈 ID를 입력해주세요.")


# ============================================================================
# Attendance 관련 추가 스키마
# ============================================================================


class AttendanceTimeSchema(Schema):
    """출퇴근 시간 변환용 스키마"""

    check_in_time = fields.Str()
    check_out_time = fields.Str()

    @validates("check_in_time")
    def validate_check_in_time(self, value):
        if value:
            try:
                datetime.strptime(value, "%H:%M")
            except ValueError:
                raise ValidationError("출근 시간은 HH:MM 형식이어야 합니다.")

    @validates("check_out_time")
    def validate_check_out_time(self, value):
        if value:
            try:
                datetime.strptime(value, "%H:%M")
            except ValueError:
                raise ValidationError("퇴근 시간은 HH:MM 형식이어야 합니다.")


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
password_change_schema = PasswordChangeSchema()
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

# 추가 검증용 스키마
task_update_schema = TaskUpdateSchema()
irregular_task_create_schema = IrregularTaskCreateSchema()
unchecked_resolve_schema = UncheckedResolveSchema()
notice_read_create_schema = NoticeReadCreateSchema()
notice_delete_schema = NoticeDeleteSchema()
issue_resolve_schema = IssueResolveSchema()
attendance_time_schema = AttendanceTimeSchema()
notification_query_schema = NotificationQuerySchema()

# 응답 래퍼 스키마
response_schema = ResponseSchema()
error_schema = ErrorSchema()
pagination_schema = PaginationSchema()
