from datetime import datetime
from marshmallow import Schema, fields, validates, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.models import TrainingInfo


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
    start_date = fields.Str()  # 모델에서 nullable=True
    end_date = fields.Str()    # 모델에서 nullable=True
    dept = fields.Str()        # 모델에서 nullable=True
    manager_name = fields.Str() # 모델에서 nullable=True

    @validates("start_date")
    def validate_start_date(self, value):
        if value:  # None이 아닌 경우만 검증
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                raise ValidationError("시작 날짜는 YYYY-MM-DD 형식이어야 합니다.")

    @validates("end_date")
    def validate_end_date(self, value):
        if value:  # None이 아닌 경우만 검증
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
# 스키마 인스턴스 생성
# ============================================================================

training_info_schema = TrainingInfoSchema()
training_infos_schema = TrainingInfoSchema(many=True)
training_info_create_schema = TrainingInfoCreateSchema()
training_info_update_schema = TrainingInfoUpdateSchema()
