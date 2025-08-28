from datetime import datetime
from marshmallow import Schema, fields, validates, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.models import Attendance


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
    check_in_time = fields.Str()  # 문자열로 변경
    check_out_time = fields.Str()  # 문자열로 변경
    daily_log = fields.Bool()


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


class AttendanceListFilterSchema(Schema):
    """출퇴근 기록 목록 조회 필터 검증용 스키마"""

    page = fields.Int(missing=1, validate=lambda x: x > 0)
    per_page = fields.Int(missing=10, validate=lambda x: 1 <= x <= 100)
    year = fields.Int()
    month = fields.Int(validate=lambda x: 1 <= x <= 12)
    instructor = fields.Str()
    training_course = fields.Str()
    search = fields.Str()

    @validates("month")
    def validate_month(self, value):
        if value and (value < 1 or value > 12):
            raise ValidationError("월은 1부터 12 사이의 값이어야 합니다.")


# ============================================================================
# 스키마 인스턴스 생성
# ============================================================================

attendance_schema = AttendanceSchema()
attendances_schema = AttendanceSchema(many=True)
attendance_create_schema = AttendanceCreateSchema()
attendance_time_schema = AttendanceTimeSchema()
attendance_list_filter_schema = AttendanceListFilterSchema()
