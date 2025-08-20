"""
Unchecked service for unchecked item-related business logic
"""

from typing import Dict, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from .base_service import BaseService
from app.models.models import (
    UncheckedDescription,
    UncheckedComment,
    TaskItem,
    TrainingInfo,
)


class UncheckedService(BaseService):
    """미체크 항목 관련 비즈니스 로직 처리"""

    @staticmethod
    def get_irregular_tasks(session: Session) -> List[Dict]:
        """비정기 업무 목록 조회"""
        UncheckedService.validate_session(session)

        # 가장 최근 상태만 조회 (resolved=False인 항목들)
        tasks_query = (
            session.query(UncheckedDescription)
            .filter(UncheckedDescription.resolved == False)
            .order_by(UncheckedDescription.created_at.desc())
        )

        tasks = []
        for task in tasks_query.all():
            tasks.append(
                {
                    "id": task.id,
                    "task_name": task.content,
                    "is_checked": task.resolved,
                    "checked_date": task.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "training_course": task.training_course,
                }
            )

        return tasks

    @staticmethod
    def create_irregular_task(
        session: Session, task_name: str, training_course: str, is_checked: bool
    ) -> UncheckedDescription:
        """비정기 업무 생성"""
        UncheckedService.validate_session(session)

        irregular_task = UncheckedDescription(
            content=task_name,
            training_course=training_course,
            resolved=is_checked,
        )

        UncheckedService.flush_and_get_id(session, irregular_task)
        return irregular_task

    @staticmethod
    def save_irregular_tasks(session: Session, validated_data: Dict) -> None:
        """비정기 업무 저장"""
        UncheckedService.validate_session(session)

        training_course = validated_data["training_course"]
        updates = validated_data["updates"]

        for update in updates:
            task_name = update.get("task_name")
            is_checked = update.get("is_checked")

            # 비정기 업무 생성
            UncheckedService.create_irregular_task(
                session, task_name, training_course, is_checked
            )

    @staticmethod
    def get_unchecked_descriptions(
        session: Session, include_resolved: bool = False
    ) -> List[Dict]:
        """미체크 항목 설명 및 액션 플랜 조회 (부서명 포함)"""
        UncheckedService.validate_session(session)

        query = session.query(UncheckedDescription)
        if not include_resolved:
            query = query.filter(UncheckedDescription.resolved == False)

        items = query.order_by(UncheckedDescription.created_at.desc()).all()

        unchecked_items = []
        for item in items:
            # 부서명 조회
            dept = None
            if item.training_course:
                training_info = (
                    session.query(TrainingInfo)
                    .filter(TrainingInfo.training_course == item.training_course)
                    .first()
                )
                if training_info:
                    dept = training_info.dept

            # due days 조회 (task_items에서 매칭되는 항목 찾기)
            due_days = 3  # 기본값
            if item.content:
                # 미체크 사유에서 작업명 추출 시도
                task_items = session.query(TaskItem).all()
                for task_item in task_items:
                    if task_item.task_name in item.content:
                        due_days = task_item.due or 3
                        break

            # 마감일 계산
            deadline = item.created_at.date() + timedelta(days=due_days)
            is_overdue = datetime.now().date() > deadline

            unchecked_items.append(
                {
                    "id": item.id,
                    "content": item.content,
                    "action_plan": item.action_plan,
                    "training_course": item.training_course,
                    "dept": dept,
                    "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "resolved": item.resolved,
                    "due_days": due_days,
                    "deadline": deadline.strftime("%Y-%m-%d"),
                    "is_overdue": is_overdue,
                }
            )

        return unchecked_items

    @staticmethod
    def create_unchecked_description(
        session: Session, description_data: Dict
    ) -> UncheckedDescription:
        """미체크 항목 설명과 액션 플랜 저장"""
        UncheckedService.validate_session(session)

        unchecked_description = UncheckedDescription(
            content=description_data["content"],
            action_plan=description_data.get("action_plan"),
            training_course=description_data.get("training_course"),
            resolved=False,
        )

        UncheckedService.flush_and_get_id(session, unchecked_description)
        return unchecked_description

    @staticmethod
    def resolve_unchecked_description(
        session: Session, validated_data: Dict
    ) -> UncheckedDescription:
        """미체크 항목 해결"""
        UncheckedService.validate_session(session)

        unchecked_id = validated_data["unchecked_id"]

        unchecked_item = UncheckedService.safe_get_by_id(
            session,
            UncheckedDescription,
            unchecked_id,
            "미체크 항목을 찾을 수 없습니다.",
        )

        if unchecked_item.resolved:
            raise ValueError("이미 해결된 항목입니다.")

        unchecked_item.resolved = True
        return unchecked_item

    @staticmethod
    def add_unchecked_comment(session: Session, comment_data: Dict) -> UncheckedComment:
        """미체크 항목에 댓글 추가"""
        UncheckedService.validate_session(session)

        # 미체크 항목 존재 확인
        UncheckedService.safe_get_by_id(
            session,
            UncheckedDescription,
            comment_data["unchecked_id"],
            "미체크 항목을 찾을 수 없습니다.",
        )

        unchecked_comment = UncheckedComment(
            unchecked_id=comment_data["unchecked_id"],
            comment=comment_data["comment"],
        )

        UncheckedService.flush_and_get_id(session, unchecked_comment)
        return unchecked_comment

    @staticmethod
    def get_unchecked_comments(session: Session, unchecked_id: int) -> List[Dict]:
        """미체크 항목의 댓글 조회"""
        UncheckedService.validate_session(session)

        # 미체크 항목 존재 확인
        UncheckedService.safe_get_by_id(
            session,
            UncheckedDescription,
            unchecked_id,
            "미체크 항목을 찾을 수 없습니다.",
        )

        comments_query = (
            session.query(UncheckedComment)
            .filter(UncheckedComment.unchecked_id == unchecked_id)
            .order_by(UncheckedComment.created_at.asc())
        )

        comments = [
            {
                "id": comment.id,
                "comment": comment.comment,
                "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "unchecked_id": comment.unchecked_id,
            }
            for comment in comments_query.all()
        ]

        return comments

    @staticmethod
    def get_unchecked_by_id(
        session: Session, unchecked_id: int
    ) -> UncheckedDescription:
        """ID로 미체크 항목 조회"""
        return UncheckedService.safe_get_by_id(
            session,
            UncheckedDescription,
            unchecked_id,
            "미체크 항목을 찾을 수 없습니다.",
        )

    @staticmethod
    def get_unchecked_by_course(
        session: Session, training_course: str, include_resolved: bool = False
    ) -> List[UncheckedDescription]:
        """교육과정별 미체크 항목 조회"""
        UncheckedService.validate_session(session)

        query = session.query(UncheckedDescription).filter(
            UncheckedDescription.training_course == training_course
        )

        if not include_resolved:
            query = query.filter(UncheckedDescription.resolved == False)

        return query.order_by(UncheckedDescription.created_at.desc()).all()

    @staticmethod
    def update_unchecked_description(
        session: Session, unchecked_id: int, update_data: Dict
    ) -> UncheckedDescription:
        """미체크 항목 정보 업데이트"""
        unchecked_item = UncheckedService.safe_get_by_id(
            session,
            UncheckedDescription,
            unchecked_id,
            "미체크 항목을 찾을 수 없습니다.",
        )

        # 업데이트할 필드들 적용
        allowed_fields = ["content", "action_plan", "training_course"]
        for field, value in update_data.items():
            if field in allowed_fields and hasattr(unchecked_item, field):
                setattr(unchecked_item, field, value)

        return unchecked_item

    @staticmethod
    def delete_comment(session: Session, comment_id: int) -> None:
        """댓글 삭제"""
        comment = UncheckedService.safe_get_by_id(
            session, UncheckedComment, comment_id, "댓글을 찾을 수 없습니다."
        )
        session.delete(comment)

    @staticmethod
    def get_overdue_items(session: Session) -> List[Dict]:
        """마감일이 지난 미체크 항목들 조회"""
        UncheckedService.validate_session(session)

        today = datetime.now().date()
        items = (
            session.query(UncheckedDescription)
            .filter(UncheckedDescription.resolved == False)
            .all()
        )

        overdue_items = []
        for item in items:
            # due days 계산
            due_days = 3  # 기본값
            if item.content:
                task_items = session.query(TaskItem).all()
                for task_item in task_items:
                    if task_item.task_name in item.content:
                        due_days = task_item.due or 3
                        break

            deadline = item.created_at.date() + timedelta(days=due_days)
            if today > deadline:
                overdue_items.append(
                    {
                        "id": item.id,
                        "content": item.content,
                        "training_course": item.training_course,
                        "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        "deadline": deadline.strftime("%Y-%m-%d"),
                        "days_overdue": (today - deadline).days,
                    }
                )

        return overdue_items
