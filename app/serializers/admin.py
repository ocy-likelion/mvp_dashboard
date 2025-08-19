from typing import Dict, List, Optional
from datetime import datetime, timedelta

from .base import Serializer
from app.schemas import training_info_schema, training_infos_schema
from app.models.models import TaskChecklist, TrainingInfo


class AdminSerializer:
    """관리자 관련 직렬화 함수들"""

    @staticmethod
    def serialize_training_info(training_info) -> Dict:
        """단일 훈련 정보 직렬화"""
        return Serializer.serialize(training_info, training_info_schema)

    @staticmethod
    def serialize_training_infos(training_infos: List) -> List[Dict]:
        """여러 훈련 정보 직렬화"""
        return Serializer.serialize(training_infos, training_infos_schema, many=True)

    @staticmethod
    def calculate_check_rate(total_tasks: int, checked_tasks: int) -> float:
        """체크율 계산"""
        if total_tasks <= 0:
            return 0.0
        return round((checked_tasks / total_tasks) * 100, 2)

    @staticmethod
    def get_daily_task_status(session, target_date: datetime = None) -> List[Dict]:
        """특정 날짜의 훈련 과정별 업무 체크 상태 조회"""
        if target_date is None:
            target_date = datetime.now().date()
        
        # 모든 훈련 과정 조회
        training_courses = session.query(TrainingInfo).all()
        task_status = []

        for course in training_courses:
            # 특정 날짜의 체크된 데이터만 필터링
            daily_checklist = (
                session.query(TaskChecklist)
                .filter(
                    TaskChecklist.training_course == course.training_course,
                    TaskChecklist.checked_date >= target_date,
                    TaskChecklist.checked_date < target_date + timedelta(days=1),
                )
                .all()
            )

            total_tasks = len(daily_checklist)
            checked_tasks = sum(1 for task in daily_checklist if task.is_checked)
            check_rate = AdminSerializer.calculate_check_rate(total_tasks, checked_tasks)

            task_status.append({
                "training_course": course.training_course,
                "dept": course.dept,
                "check_rate": f"{check_rate}%",
            })

        return task_status

    @staticmethod
    def get_overall_task_status(session) -> List[Dict]:
        """훈련 과정별 전체 체크율 조회"""
        training_courses = session.query(TrainingInfo).all()
        task_status = []

        for course in training_courses:
            # 전체 체크리스트 데이터
            all_checklist = (
                session.query(TaskChecklist)
                .filter(TaskChecklist.training_course == course.training_course)
                .all()
            )

            total_tasks = len(all_checklist)
            checked_tasks = sum(1 for task in all_checklist if task.is_checked)
            check_rate = AdminSerializer.calculate_check_rate(total_tasks, checked_tasks)

            task_status.append({
                "training_course": course.training_course,
                "dept": course.dept,
                "check_rate": f"{check_rate}%",
            })

        return task_status

    @staticmethod
    def get_combined_task_status(session) -> List[Dict]:
        """훈련 과정별 통합 업무 체크율 조회 (당일, 전날, 전체)"""
        # 종료된 지 1주일 이내의 과정만 포함
        one_week_ago = datetime.now().date() - timedelta(days=7)
        training_courses = (
            session.query(TrainingInfo)
            .filter(TrainingInfo.end_date >= one_week_ago)
            .order_by(TrainingInfo.end_date.desc())
            .all()
        )

        task_status = []
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        for course in training_courses:
            # 전체 체크리스트 데이터
            all_checklist = (
                session.query(TaskChecklist)
                .filter(TaskChecklist.training_course == course.training_course)
                .all()
            )

            # 당일 체크리스트 데이터
            daily_checklist = [
                task
                for task in all_checklist
                if task.checked_date and task.checked_date.date() == today
            ]

            # 전날 체크리스트 데이터
            yesterday_checklist = [
                task
                for task in all_checklist
                if task.checked_date and task.checked_date.date() == yesterday
            ]

            # 체크율 계산
            total_tasks = len(all_checklist)
            checked_tasks = sum(1 for task in all_checklist if task.is_checked)
            overall_check_rate = AdminSerializer.calculate_check_rate(total_tasks, checked_tasks)

            daily_total_tasks = len(daily_checklist)
            daily_checked_tasks = sum(1 for task in daily_checklist if task.is_checked)
            daily_check_rate = AdminSerializer.calculate_check_rate(daily_total_tasks, daily_checked_tasks)

            yesterday_total_tasks = len(yesterday_checklist)
            yesterday_checked_tasks = sum(1 for task in yesterday_checklist if task.is_checked)
            yesterday_check_rate = AdminSerializer.calculate_check_rate(yesterday_total_tasks, yesterday_checked_tasks)

            task_status.append({
                "training_course": course.training_course,
                "dept": course.dept,
                "manager_name": course.manager_name or "담당자 없음",
                "daily_check_rate": f"{daily_check_rate}%",
                "yesterday_check_rate": f"{yesterday_check_rate}%",
                "overall_check_rate": f"{overall_check_rate}%",
            })

        return task_status

    @staticmethod
    def validate_date_filter(date_str: Optional[str] = None) -> datetime:
        """날짜 필터 검증"""
        if date_str is None:
            return datetime.now().date()
        
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            raise ValueError("날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식을 사용해주세요.")
