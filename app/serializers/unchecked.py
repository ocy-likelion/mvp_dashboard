from typing import Dict, List
from datetime import datetime, timedelta

from .base import Serializer
from app.schemas import (
    unchecked_description_schema,
    unchecked_descriptions_schema,
    unchecked_comment_schema,
    unchecked_comments_schema,
    unchecked_description_create_schema,
    unchecked_comment_create_schema,
    unchecked_resolve_schema,
    irregular_task_create_schema,
)
from app.models.models import (
    UncheckedDescription,
    UncheckedComment,
    TaskItem,
    TrainingInfo,
)


class UncheckedSerializer:
    """미해결 항목 관련 직렬화 함수들"""

    @staticmethod
    def serialize_unchecked_description(description) -> Dict:
        """단일 미해결 항목 직렬화"""
        return Serializer.serialize(description, unchecked_description_schema)

    @staticmethod
    def serialize_unchecked_descriptions(descriptions: List) -> List[Dict]:
        """여러 미해결 항목 직렬화"""
        return Serializer.serialize(
            descriptions, unchecked_descriptions_schema, many=True
        )

    @staticmethod
    def serialize_unchecked_comment(comment) -> Dict:
        """단일 미해결 댓글 직렬화"""
        return Serializer.serialize(comment, unchecked_comment_schema)

    @staticmethod
    def serialize_unchecked_comments(comments: List) -> List[Dict]:
        """여러 미해결 댓글 직렬화"""
        return Serializer.serialize(comments, unchecked_comments_schema, many=True)

    @staticmethod
    def deserialize_unchecked_description_create(data: Dict) -> Dict:
        """미해결 항목 생성 데이터 역직렬화"""
        return Serializer.deserialize(data, unchecked_description_create_schema)

    @staticmethod
    def deserialize_unchecked_comment_create(data: Dict) -> Dict:
        """미해결 댓글 생성 데이터 역직렬화"""
        return Serializer.deserialize(data, unchecked_comment_create_schema)

    @staticmethod
    def deserialize_unchecked_resolve(data: Dict) -> Dict:
        """미해결 항목 해결 데이터 역직렬화"""
        return Serializer.deserialize(data, unchecked_resolve_schema)

    @staticmethod
    def deserialize_irregular_task_create(data: Dict) -> Dict:
        """불규칙 업무 생성 데이터 역직렬화"""
        return Serializer.deserialize(data, irregular_task_create_schema)

    @staticmethod
    def get_irregular_tasks(session) -> List[Dict]:
        """비정기 업무 목록 조회"""
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
                }
            )

        return tasks

    @staticmethod
    def create_irregular_task(
        session, task_name: str, training_course: str, is_checked: bool
    ):
        """비정기 업무 생성"""
        irregular_task = UncheckedDescription(
            content=task_name,
            training_course=training_course,
            resolved=is_checked,
        )
        session.add(irregular_task)
        return irregular_task

    @staticmethod
    def save_irregular_tasks(session, data: Dict):
        """비정기 업무 저장"""
        # 데이터 검증
        validated_data = UncheckedSerializer.deserialize_irregular_task_create(data)

        for update in validated_data["updates"]:
            task_name = update.get("task_name")
            is_checked = update.get("is_checked")

            # Serializer를 사용한 비정기 업무 생성
            UncheckedSerializer.create_irregular_task(
                session, task_name, validated_data["training_course"], is_checked
            )

    @staticmethod
    def get_unchecked_descriptions(session) -> List[Dict]:
        """미체크 항목 설명 및 액션 플랜 조회 (부서명 포함)"""
        unchecked_items = []
        items = (
            session.query(UncheckedDescription)
            .filter(UncheckedDescription.resolved == False)
            .order_by(UncheckedDescription.created_at.desc())
            .all()
        )

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
                task_item = (
                    session.query(TaskItem)
                    .filter(
                        TaskItem.task_name.in_(
                            [
                                task_name
                                for task_name in session.query(TaskItem.task_name).all()
                            ]
                        )
                    )
                    .filter(
                        item.content.like(f"%{TaskItem.task_name}%에 대한 미체크 사유")
                    )
                    .first()
                )
                if task_item:
                    due_days = task_item.due or 3

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
    def save_unchecked_description(session, data: Dict):
        """미체크 항목 설명과 액션 플랜 저장"""
        # 데이터 검증
        validated_data = UncheckedSerializer.deserialize_unchecked_description_create(
            data
        )

        unchecked_description = UncheckedDescription(
            content=validated_data["content"],
            action_plan=validated_data.get("action_plan"),
            training_course=validated_data.get("training_course"),
            resolved=False,
        )

        session.add(unchecked_description)
        return unchecked_description

    @staticmethod
    def resolve_unchecked_description(session, data: Dict):
        """미체크 항목 해결"""
        # 데이터 검증
        validated_data = UncheckedSerializer.deserialize_unchecked_resolve(data)

        unchecked_item = (
            session.query(UncheckedDescription)
            .filter(UncheckedDescription.id == validated_data["unchecked_id"])
            .first()
        )

        if not unchecked_item:
            raise ValueError("미체크 항목을 찾을 수 없습니다.")

        unchecked_item.resolved = True
        return unchecked_item

    @staticmethod
    def add_unchecked_comment(session, data: Dict):
        """미체크 항목에 댓글 추가"""
        # 데이터 검증
        validated_data = UncheckedSerializer.deserialize_unchecked_comment_create(data)

        unchecked_comment = UncheckedComment(
            unchecked_id=validated_data["unchecked_id"],
            comment=validated_data["comment"],
        )

        session.add(unchecked_comment)
        return unchecked_comment

    @staticmethod
    def get_unchecked_comments(session, unchecked_id: int) -> List[Dict]:
        """미체크 항목의 댓글 조회"""
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
            }
            for comment in comments_query.all()
        ]

        return comments
