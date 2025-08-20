"""
Task service for task-related business logic
"""

from typing import Dict, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from .base_service import BaseService
from app.models.models import TaskItem, TaskChecklist


class TaskService(BaseService):
    """작업 관련 비즈니스 로직 처리"""

    @staticmethod
    def save_task_checklist(session: Session, validated_data: Dict) -> None:
        """체크리스트 저장/업데이트"""
        BaseService.validate_db_session(session)

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
                session.query(TaskItem).filter(TaskItem.task_name == task_name).first()
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
    def update_task_checklist(session: Session, validated_data: Dict) -> Dict:
        """체크리스트 업데이트 (당일 데이터만)"""
        BaseService.validate_db_session(session)

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
            raise ValueError("당일 저장된 체크리스트가 없어 업데이트할 수 없습니다.")
            
        return {"updated_count": updated_count, "not_found_items": not_found_items}

    @staticmethod
    def get_tasks(session: Session, task_category: str = None) -> List[TaskItem]:
        """업무 체크리스트 조회"""
        BaseService.validate_db_session(session)

        # ORM을 사용하여 업무 조회
        tasks_query = session.query(TaskItem).order_by(TaskItem.id.asc())

        if task_category:
            tasks_query = tasks_query.filter(TaskItem.task_category == task_category)

        return tasks_query.all()

    @staticmethod
    def get_task_by_name(session: Session, task_name: str) -> TaskItem:
        """작업명으로 작업 조회"""
        BaseService.validate_db_session(session)

        task = session.query(TaskItem).filter(TaskItem.task_name == task_name).first()
        if not task:
            raise ValueError(f"작업을 찾을 수 없습니다: {task_name}")

        return task

    @staticmethod
    def create_task_item(session: Session, task_data: Dict) -> TaskItem:
        """새 작업 항목 생성"""
        BaseService.validate_db_session(session)

        # 중복 체크
        existing_task = (
            session.query(TaskItem)
            .filter(TaskItem.task_name == task_data["task_name"])
            .first()
        )
        if existing_task:
            raise ValueError("이미 존재하는 작업명입니다.")

        task = TaskItem(
            task_name=task_data["task_name"],
            task_category=task_data.get("task_category"),
            due=task_data.get("due", 3),  # 기본 마감일 3일
            description=task_data.get("description"),
        )

        TaskService.flush_and_get_id(session, task)
        return task

    @staticmethod
    def get_checklist_status(
        session: Session, training_course: str, date: datetime = None
    ) -> List[Dict]:
        """특정 과정의 체크리스트 상태 조회"""
        BaseService.validate_db_session(session)

        if date is None:
            date = datetime.now().date()

        # 해당 날짜의 체크리스트 데이터 조회
        checklists = (
            session.query(TaskChecklist)
            .join(TaskItem, TaskChecklist.task_id == TaskItem.id)
            .filter(
                TaskChecklist.training_course == training_course,
                TaskChecklist.checked_date >= date,
                TaskChecklist.checked_date < date + timedelta(days=1),
            )
            .all()
        )

        status_list = []
        for checklist in checklists:
            task = (
                session.query(TaskItem).filter(TaskItem.id == checklist.task_id).first()
            )
            if task:
                status_list.append(
                    {
                        "task_name": task.task_name,
                        "task_category": task.task_category,
                        "is_checked": checklist.is_checked,
                        "checked_date": checklist.checked_date.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "username": checklist.username,
                    }
                )

        return status_list

    @staticmethod
    def get_unchecked_tasks(
        session: Session, training_course: str, date: datetime = None
    ) -> List[Dict]:
        """미체크 작업 목록 조회"""
        BaseService.validate_db_session(session)

        if date is None:
            date = datetime.now().date()

        # 모든 작업 목록
        all_tasks = session.query(TaskItem).all()

        # 해당 날짜에 체크된 작업들
        checked_task_ids = (
            session.query(TaskChecklist.task_id)
            .filter(
                TaskChecklist.training_course == training_course,
                TaskChecklist.checked_date >= date,
                TaskChecklist.checked_date < date + timedelta(days=1),
                TaskChecklist.is_checked == True,
            )
            .all()
        )
        checked_ids = [task_id[0] for task_id in checked_task_ids]

        # 미체크 작업들 필터링
        unchecked_tasks = []
        for task in all_tasks:
            if task.id not in checked_ids:
                unchecked_tasks.append(
                    {
                        "task_id": task.id,
                        "task_name": task.task_name,
                        "task_category": task.task_category,
                        "due": task.due,
                        "description": task.description,
                    }
                )

        return unchecked_tasks
