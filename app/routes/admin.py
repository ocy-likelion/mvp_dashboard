from flask import Blueprint, request, jsonify
import logging
from app.models.db import get_db_session
from app.models.models import TaskChecklist, TrainingInfo
from datetime import datetime, timedelta
from app.serializers import (
    json_response,
    error_json_response,
)

admin_bp = Blueprint("admin", __name__)
logger = logging.getLogger(__name__)


@admin_bp.route("/admin/task_status", methods=["GET"])
def get_task_status():
    """
    훈련 과정별 업무 체크리스트의 체크율을 조회하는 API
    ---
    tags:
      - Admin
    summary: "훈련 과정별 업무 체크 상태 및 부서 정보 조회"
    responses:
      200:
        description: 훈련 과정별 체크율 데이터를 반환
      500:
        description: 체크 상태 조회 실패
    """
    try:
        session = get_db_session()

        # 당일 날짜
        today = datetime.now().date()

        # 훈련 과정별 체크 상태 조회
        task_status = []

        # 모든 훈련 과정 조회
        training_courses = session.query(TrainingInfo).all()

        for course in training_courses:
            # 당일 체크된 데이터만 필터링
            daily_checklist = (
                session.query(TaskChecklist)
                .filter(
                    TaskChecklist.training_course == course.training_course,
                    TaskChecklist.checked_date >= today,
                    TaskChecklist.checked_date < today + timedelta(days=1),
                )
                .all()
            )

            total_tasks = len(daily_checklist)
            checked_tasks = sum(1 for task in daily_checklist if task.is_checked)
            check_rate = (
                round((checked_tasks / total_tasks) * 100, 2) if total_tasks > 0 else 0
            )

            task_status.append(
                {
                    "training_course": course.training_course,
                    "dept": course.dept,
                    "check_rate": f"{check_rate}%",
                }
            )

        session.close()

        return json_response(
            data=task_status, message="업무 체크 상태 조회 성공", status_code=200
        )
    except Exception as e:
        logger.error("Error retrieving task status", exc_info=True)
        return error_json_response("업무 체크 상태 조회 실패", status_code=500)


@admin_bp.route("/admin/task_status_overall", methods=["GET"])
def get_overall_task_status():
    """
    훈련 과정별 전체 체크율을 조회하는 API
    ---
    tags:
      - Admin
    responses:
      200:
        description: 훈련 과정별 전체 체크율 데이터 반환
      500:
        description: 체크율 조회 실패
    """
    try:
        session = get_db_session()

        task_status = []

        # 모든 훈련 과정 조회
        training_courses = session.query(TrainingInfo).all()

        for course in training_courses:
            # 전체 체크리스트 데이터
            all_checklist = (
                session.query(TaskChecklist)
                .filter(TaskChecklist.training_course == course.training_course)
                .all()
            )

            total_tasks = len(all_checklist)
            checked_tasks = sum(1 for task in all_checklist if task.is_checked)
            check_rate = (
                round((checked_tasks / total_tasks) * 100, 2) if total_tasks > 0 else 0
            )

            task_status.append(
                {
                    "training_course": course.training_course,
                    "dept": course.dept,
                    "check_rate": f"{check_rate}%",
                }
            )

        session.close()

        return json_response(
            data=task_status, message="전체 업무 체크 상태 조회 성공", status_code=200
        )
    except Exception as e:
        logger.error("Error retrieving overall task status", exc_info=True)
        return error_json_response("전체 업무 체크 상태 조회 실패", status_code=500)


@admin_bp.route("/admin/task_status_combined", methods=["GET"])
def get_combined_task_status():
    """
    훈련 과정별 업무 체크리스트의 체크율(당일, 전날, 전체)을 조회하는 API
    ---
    tags:
      - Admin
    summary: "훈련 과정별 업무 체크율 조회"
    description: "각 훈련 과정별로 담당자, 당일 체크율, 전날 체크율, 전체 체크율을 조회합니다."
    responses:
      200:
        description: 훈련 과정별 체크율 데이터 반환
      500:
        description: 체크 상태 조회 실패
    """
    try:
        session = get_db_session()

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
            overall_check_rate = (
                round((checked_tasks / total_tasks) * 100, 2) if total_tasks > 0 else 0
            )

            daily_total_tasks = len(daily_checklist)
            daily_checked_tasks = sum(1 for task in daily_checklist if task.is_checked)
            daily_check_rate = (
                round((daily_checked_tasks / daily_total_tasks) * 100, 2)
                if daily_total_tasks > 0
                else 0
            )

            yesterday_total_tasks = len(yesterday_checklist)
            yesterday_checked_tasks = sum(
                1 for task in yesterday_checklist if task.is_checked
            )
            yesterday_check_rate = (
                round((yesterday_checked_tasks / yesterday_total_tasks) * 100, 2)
                if yesterday_total_tasks > 0
                else 0
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

        session.close()

        return json_response(
            data=task_status, message="통합 업무 체크 상태 조회 성공", status_code=200
        )
    except Exception as e:
        logger.error("Error retrieving combined task status", exc_info=True)
        return error_json_response("통합 업무 체크 상태 조회 실패", status_code=500)
