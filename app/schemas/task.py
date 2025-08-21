from marshmallow import Schema, fields, validates, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.models import TaskItem, TaskChecklist


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


class TaskFilterSchema(Schema):
    """작업 필터 검증용 스키마"""

    task_category = fields.Str(
        required=False,
        allow_none=True,
        load_default=None,
        dump_default=None,
    )


# ============================================================================
# 스키마 인스턴스 생성
# ============================================================================

task_item_schema = TaskItemSchema()
task_items_schema = TaskItemSchema(many=True)
task_checklist_schema = TaskChecklistSchema()
task_checklists_schema = TaskChecklistSchema(many=True)
task_item_create_schema = TaskItemCreateSchema()
task_checklist_create_schema = TaskChecklistCreateSchema()
task_update_schema = TaskUpdateSchema()
irregular_task_create_schema = IrregularTaskCreateSchema()
task_filter_schema = TaskFilterSchema()
