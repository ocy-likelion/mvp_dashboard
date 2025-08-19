from typing import Dict, List
from datetime import datetime, timedelta

from .base import Serializer
from app.schemas import (
    task_item_schema,
    task_items_schema,
    task_checklist_schema,
    task_checklists_schema,
    task_item_create_schema,
    task_checklist_create_schema,
    task_update_schema,
    irregular_task_create_schema,
)
from app.models.models import TaskItem, TaskChecklist


class TaskSerializer:
    """작업 관련 직렬화 함수들"""

    @staticmethod
    def serialize_task_item(task_item) -> Dict:
        """단일 작업 항목 직렬화"""
        return Serializer.serialize(task_item, task_item_schema)

    @staticmethod
    def serialize_task_items(task_items: List) -> List[Dict]:
        """여러 작업 항목 직렬화"""
        return Serializer.serialize(task_items, task_items_schema, many=True)

    @staticmethod
    def serialize_task_checklist(checklist) -> Dict:
        """단일 작업 체크리스트 직렬화"""
        return Serializer.serialize(checklist, task_checklist_schema)

    @staticmethod
    def serialize_task_checklists(checklists: List) -> List[Dict]:
        """여러 작업 체크리스트 직렬화"""
        return Serializer.serialize(checklists, task_checklists_schema, many=True)

    @staticmethod
    def deserialize_task_item_create(data: Dict) -> Dict:
        """작업 항목 생성 데이터 역직렬화"""
        return Serializer.deserialize(data, task_item_create_schema)

    @staticmethod
    def deserialize_task_checklist_create(data: Dict) -> Dict:
        """작업 체크리스트 생성 데이터 역직렬화"""
        return Serializer.deserialize(data, task_checklist_create_schema)

    @staticmethod
    def deserialize_task_update(data: Dict) -> Dict:
        """작업 체크리스트 업데이트 데이터 역직렬화"""
        return Serializer.deserialize(data, task_update_schema)

    @staticmethod
    def deserialize_irregular_task_create(data: Dict) -> Dict:
        """불규칙 업무 생성 데이터 역직렬화"""
        return Serializer.deserialize(data, irregular_task_create_schema)

    @staticmethod
    def save_task_checklist(session, data: Dict):
        """체크리스트 저장/업데이트"""
        # 데이터 검증
        validated_data = TaskSerializer.deserialize_task_update(data)

        # 현재 날짜 가져오기 (시간 제외)
        current_date = datetime.now().date()

        for update in validated_data["updates"]:
            task_name = update.get("task_name")
            is_checked = update.get("is_checked", False)

            # task_id 찾기
            task = (
                session.query(TaskItem).filter(TaskItem.task_name == task_name).first()
            )
            if not task:
                continue

            # 동일 날짜의 기존 데이터 확인
            existing_record = (
                session.query(TaskChecklist)
                .filter(
                    TaskChecklist.task_id == task.id,
                    TaskChecklist.training_course == validated_data["training_course"],
                    TaskChecklist.checked_date >= current_date,
                    TaskChecklist.checked_date < current_date + timedelta(days=1),
                )
                .first()
            )

            if existing_record:
                # 기존 데이터가 있으면 업데이트
                existing_record.is_checked = is_checked
                existing_record.checked_date = datetime.now()
                existing_record.username = validated_data["username"]
            else:
                # 기존 데이터가 없으면 새로 삽입
                checklist = TaskChecklist(
                    task_id=task.id,
                    training_course=validated_data["training_course"],
                    is_checked=is_checked,
                    username=validated_data["username"],
                )
                session.add(checklist)

    @staticmethod
    def update_task_checklist(session, data: Dict) -> Dict:
        """체크리스트 업데이트 (당일 데이터만)"""
        # 데이터 검증
        validated_data = TaskSerializer.deserialize_task_update(data)

        # 현재 날짜만 사용 (시간 제외)
        today = datetime.now().date()

        updated_count = 0
        not_found_items = []

        for update in validated_data["updates"]:
            task_name = update.get("task_name")
            is_checked = update.get("is_checked", False)

            # task_id 찾기
            task = (
                session.query(TaskItem).filter(TaskItem.task_name == task_name).first()
            )
            if not task:
                not_found_items.append(task_name)
                continue

            # 당일 날짜의 기존 데이터 확인
            existing_record = (
                session.query(TaskChecklist)
                .filter(
                    TaskChecklist.task_id == task.id,
                    TaskChecklist.training_course == validated_data["training_course"],
                    TaskChecklist.checked_date >= today,
                    TaskChecklist.checked_date < today + timedelta(days=1),
                )
                .first()
            )

            if existing_record:
                # 기존 데이터가 있으면 업데이트
                existing_record.is_checked = is_checked
                existing_record.checked_date = datetime.now()
                updated_count += 1
            else:
                # 업데이트할 데이터가 없음
                not_found_items.append(task_name)

        return {"updated_count": updated_count, "not_found_items": not_found_items}

    @staticmethod
    def get_tasks(session, task_category: str = None) -> List[Dict]:
        """업무 체크리스트 조회"""
        # ORM을 사용하여 업무 조회
        tasks_query = session.query(TaskItem).order_by(TaskItem.id.asc())

        if task_category:
            tasks_query = tasks_query.filter(TaskItem.task_category == task_category)

        tasks = tasks_query.all()

        # Serializer를 사용한 데이터 직렬화
        return TaskSerializer.serialize_task_items(tasks)
