from flask import Blueprint, request
import logging
from app.models.db import get_db_session
from app.serializers import (
    json_response,
    error_json_response,
)
from app.services import AdminService

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
    parameters:
      - name: date
        in: query
        description: 조회할 날짜 (YYYY-MM-DD 형식, 기본값은 당일)
        required: false
        type: string
    responses:
      200:
        description: 훈련 과정별 체크율 데이터를 반환
      400:
        description: 잘못된 날짜 형식
      500:
        description: 체크 상태 조회 실패
    """
    try:
        session = get_db_session()

        # 날짜 파라미터 검증
        date_str = request.args.get("date")
        try:
            target_date = AdminService.validate_date_filter(date_str)
        except ValueError as e:
            return error_json_response(str(e), status_code=400)

        # Service를 통한 데이터 조회
        task_status = AdminService.get_daily_task_status(session, target_date)

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

        # Service를 통한 데이터 조회
        task_status = AdminService.get_overall_task_status(session)

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

        # Service를 통한 데이터 조회
        task_status = AdminService.get_combined_task_status(session)

        session.close()

        return json_response(
            data=task_status, message="통합 업무 체크 상태 조회 성공", status_code=200
        )
    except Exception as e:
        logger.error("Error retrieving combined task status", exc_info=True)
        return error_json_response("통합 업무 체크 상태 조회 실패", status_code=500)
