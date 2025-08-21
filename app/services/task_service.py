"""
Task service for task-related business logic
"""

from typing import Dict, List
from datetime import datetime, timedelta

from .base_service import BaseService
from app.models.models import TaskItem, TaskChecklist
from app.utils.database import db_session, db_session_read_only


class TaskService(BaseService):
    """작업 관련 비즈니스 로직 처리"""

    @staticmethod
    def save_task_checklist(validated_data: Dict) -> None:
        """체크리스트 저장/업데이트"""
        with db_session() as session:
            training_course = validated_data["training_course"]
            username = validated_data["username"]
            updates = validated_data["updates"]

            # 현재 날짜 가져오기 (시간 제외)
            current_date = datetime.now().date()

            for update in updates:
                task_name = update.get("task_name")
                is_checked = update.get("is_checked", False)

                # task_id 찾기
                task = (
                    session.query(TaskItem)
                    .filter(TaskItem.task_name == task_name)
                    .first()
                )
                if not task:
                    continue

                # 동일 날짜의 기존 데이터 확인
                existing_record = (
                    session.query(TaskChecklist)
                    .filter(
                        TaskChecklist.task_id == task.id,
                        TaskChecklist.training_course == training_course,
                        TaskChecklist.checked_date >= current_date,
                        TaskChecklist.checked_date < current_date + timedelta(days=1),
                    )
                    .first()
                )

                if existing_record:
                    # 기존 데이터가 있으면 업데이트
                    existing_record.is_checked = is_checked
                    existing_record.checked_date = datetime.now()
                    existing_record.username = username
                else:
                    # 기존 데이터가 없으면 새로 삽입
                    checklist = TaskChecklist(
                        task_id=task.id,
                        training_course=training_course,
                        is_checked=is_checked,
                        username=username,
                    )
                    session.add(checklist)

    @staticmethod
    def update_task_checklist(validated_data: Dict) -> Dict:
        """체크리스트 업데이트 (당일 데이터만)"""
        with db_session() as session:
            training_course = validated_data["training_course"]
            updates = validated_data["updates"]

            # 현재 날짜만 사용 (시간 제외)
            today = datetime.now().date()

            updated_count = 0
            not_found_items = []

            for update in updates:
                task_name = update.get("task_name")
                is_checked = update.get("is_checked", False)

                # task_id 찾기
                task = (
                    session.query(TaskItem)
                    .filter(TaskItem.task_name == task_name)
                    .first()
                )
                if not task:
                    not_found_items.append(task_name)
                    continue

                # 당일 날짜의 기존 데이터 확인
                existing_record = (
                    session.query(TaskChecklist)
                    .filter(
                        TaskChecklist.task_id == task.id,
                        TaskChecklist.training_course == training_course,
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

            # 비즈니스 규칙: 업데이트된 항목이 없으면 예외 발생
            if updated_count == 0:
                raise ValueError(
                    "당일 저장된 체크리스트가 없어 업데이트할 수 없습니다."
                )

            return {"updated_count": updated_count, "not_found_items": not_found_items}

    @staticmethod
    def get_tasks(validated_data: Dict) -> List[Dict]:
        """업무 체크리스트 조회"""
        task_category = validated_data.get("task_category")

        with db_session_read_only() as session:
            tasks_query = session.query(TaskItem).order_by(TaskItem.id.asc())

            if task_category:
                tasks_query = tasks_query.filter(
                    TaskItem.task_category == task_category
                )

            tasks = tasks_query.all()

            return tasks
