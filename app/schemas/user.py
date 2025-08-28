import re
from marshmallow import Schema, fields, validates, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.models import User, UserLastCheck


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
# 스키마 인스턴스 생성
# ============================================================================

# User 관련 스키마 인스턴스
user_schema = UserSchema()
users_schema = UserSchema(many=True)
user_create_schema = UserCreateSchema()
user_update_schema = UserUpdateSchema()
user_login_schema = UserLoginSchema()
password_change_schema = PasswordChangeSchema()

# UserLastCheck 관련 스키마 인스턴스
user_last_check_schema = UserLastCheckSchema()
user_last_checks_schema = UserLastCheckSchema(many=True)
user_last_check_update_schema = UserLastCheckUpdateSchema()
