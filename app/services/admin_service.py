"""
Admin service for admin-related business logic
"""

from typing import Dict, List
from datetime import datetime, timedelta

from .base_service import BaseService
from app.models.models import TaskChecklist, TrainingInfo
from app.utils.database import db_session_read_only


class AdminService(BaseService):
    """관리자 관련 비즈니스 로직 처리"""

    @staticmethod
    def calculate_check_rate(total_tasks: int, checked_tasks: int) -> float:
        """체크율 계산"""
        if total_tasks <= 0:
            return 0.0
        return round((checked_tasks / total_tasks) * 100, 2)

    @staticmethod
    def get_daily_task_status(validated_data: Dict) -> Dict:
        """특정 날짜의 훈련 과정별 업무 체크 상태 조회"""
        target_date = validated_data.get("date")
        if target_date is None:
            target_date = datetime.now().date()

        with db_session_read_only() as session:
            # 모든 훈련 과정 조회
            training_courses = session.query(TrainingInfo).all()
            task_status_list = []

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
                check_rate = AdminService.calculate_check_rate(
                    total_tasks, checked_tasks
                )

                task_status_list.append(
                    {
                        "training_course": course.training_course,
                        "dept": course.dept,
                        "check_rate": f"{check_rate}%",
                    }
                )

            return {
                "task_status": task_status_list,
                "total_courses": len(task_status_list),
                "timestamp": datetime.now()
            }

    @staticmethod
    def get_overall_task_status() -> List[Dict]:
        """훈련 과정별 전체 체크율 조회"""
        with db_session_read_only() as session:
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
                check_rate = AdminService.calculate_check_rate(
                    total_tasks, checked_tasks
                )

                task_status.append(
                    {
                        "training_course": course.training_course,
                        "dept": course.dept,
                        "check_rate": f"{check_rate}%",
                    }
                )

            return task_status

    @staticmethod
    def get_combined_task_status() -> List[Dict]:
        """훈련 과정별 통합 업무 체크율 조회 (당일, 전날, 전체)"""
        with db_session_read_only() as session:
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
                overall_check_rate = AdminService.calculate_check_rate(
                    total_tasks, checked_tasks
                )

                daily_total_tasks = len(daily_checklist)
                daily_checked_tasks = sum(
                    1 for task in daily_checklist if task.is_checked
                )
                daily_check_rate = AdminService.calculate_check_rate(
                    daily_total_tasks, daily_checked_tasks
                )

                yesterday_total_tasks = len(yesterday_checklist)
                yesterday_checked_tasks = sum(
                    1 for task in yesterday_checklist if task.is_checked
                )
                yesterday_check_rate = AdminService.calculate_check_rate(
                    yesterday_total_tasks, yesterday_checked_tasks
                )

                task_status.append(
                    {
                        "training_course": course.training_course,
                        "dept": course.dept,
                        "manager_name": course.manager_name or "담당자 없음",
                        "daily_check_rate": f"{daily_check_rate}%",
                        "yesterday_check_rate": f"{yesterday_check_rate}%",
                        "overall_check_rate": f"{overall_check_rate}%",
                    }
                )

            return task_status
