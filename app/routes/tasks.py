from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import logging
from app.models.db import get_db_session
from app.models.models import TaskItem, TaskChecklist
from app.serializers import (
    TaskSerializer,
    json_response,
    error_json_response,
    handle_serialization_errors,
)

tasks_bp = Blueprint("tasks", __name__)
logger = logging.getLogger(__name__)


@tasks_bp.route("/tasks", methods=["GET"])
def get_tasks():
    """
    업무 체크리스트 조회 API
    ---
    tags:
      - Tasks
    summary: 업무 체크리스트 데이터 조회
    parameters:
      - name: task_category
        in: query
        type: string
        required: false
        description: "업무 체크리스트의 카테고리 (예: 개발, 디자인)"
    responses:
      200:
        description: 모든 업무 체크리스트 데이터를 반환함
      500:
        description: 서버 오류로 인해 업무 체크리스트 조회 실패
    """
    try:
        task_category = request.args.get("task_category")  # 선택적 필터링

        session = get_db_session()

        # ORM을 사용하여 업무 조회
        tasks_query = session.query(TaskItem).order_by(TaskItem.id.asc())

        if task_category:
            tasks_query = tasks_query.filter(TaskItem.task_category == task_category)

        tasks = tasks_query.all()

        # Serializer를 사용한 데이터 직렬화
        serialized_tasks = TaskSerializer.serialize_task_items(tasks)

        session.close()

        return json_response(
            data=serialized_tasks, message="업무 체크리스트 조회 성공", status_code=200
        )
    except Exception as e:
        logger.error("Error retrieving tasks", exc_info=True)
        return error_json_response("업무 체크리스트 조회 실패", status_code=500)


@tasks_bp.route("/tasks", methods=["POST"])
def save_tasks():
    """
    업무 체크리스트 저장 API (동일 날짜 데이터는 업데이트)
    ---
    tags:
      - Tasks
    parameters:
      - in: body
        name: body
        description: 저장할 체크리스트 업데이트 데이터
        required: true
        schema:
          type: object
          properties:
            updates:
              type: array
              items:
                type: object
                required:
                  - task_name
                  - is_checked
                properties:
                  task_name:
                    type: string
                  is_checked:
                    type: boolean
            training_course:
              type: string
            username:
              type: string
    responses:
      201:
        description: 업무 체크리스트 저장/업데이트 성공
      400:
        description: 요청 데이터 없음
      500:
        description: 업무 체크리스트 저장 실패
    """
    try:
        data = request.json
        updates = data.get("updates")
        training_course = data.get("training_course")
        username = data.get("username")  # 프론트엔드에서 전달받은 username

        if not updates or not training_course or not username:
            return error_json_response(
                "업데이트 데이터, 훈련 과정명, 사용자명이 모두 필요합니다.", status_code=400
            )

        session = get_db_session()
        try:
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

            session.commit()

        except Exception as e:
            session.rollback()
            logger.error(f"체크리스트 저장 중 오류: {str(e)}")
            return error_json_response("체크리스트 저장 실패", status_code=500)
        finally:
            session.close()

        return json_response(
            data=None,
            message="체크리스트가 성공적으로 저장/업데이트되었습니다!",
            status_code=201,
        )

    except Exception as e:
        logger.error("체크리스트 저장 중 오류 발생", exc_info=True)
        return error_json_response("체크리스트 저장 실패", status_code=500)


@tasks_bp.route("/tasks/update", methods=["PUT"])
def update_tasks():
    """
    당일 업무 체크리스트 업데이트 API
    ---
    tags:
      - Tasks
    summary: "당일 저장된 체크리스트를 업데이트합니다."
    parameters:
      - in: body
        name: body
        description: 업데이트할 체크리스트 데이터
        required: true
        schema:
          type: object
          properties:
            updates:
              type: array
              items:
                type: object
                required:
                  - task_name
                  - is_checked
                properties:
                  task_name:
                    type: string
                    example: "출석 체크"
                  is_checked:
                    type: boolean
                    example: true
            training_course:
              type: string
              example: "데이터 분석 스쿨 4기"
    responses:
      200:
        description: 체크리스트 업데이트 성공
      404:
        description: 업데이트할 체크리스트가 존재하지 않음
      500:
        description: 업데이트 실패
    """
    try:
        data = request.json
        updates = data.get("updates")
        training_course = data.get("training_course")

        # 현재 날짜만 사용 (시간 제외)
        today = datetime.now().date()

        if not updates or not training_course:
            return error_json_response(
                "업데이트할 데이터와 훈련 과정명이 필요합니다.", status_code=400
            )

        session = get_db_session()
        try:
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

            session.commit()

        except Exception as e:
            session.rollback()
            logger.error(f"체크리스트 업데이트 중 오류: {str(e)}")
            return error_json_response("체크리스트 업데이트 실패", status_code=500)
        finally:
            session.close()

        if updated_count == 0:
            return error_json_response(
                "당일 저장된 체크리스트가 없어 업데이트할 수 없습니다.", status_code=404
            )

        response_data = {
            "updated_count": updated_count,
        }

        if not_found_items:
            response_data["warning"] = (
                "일부 항목은 당일 저장된 데이터가 없어 업데이트되지 않았습니다."
            )
            response_data["not_found_items"] = not_found_items

        return json_response(
            data=response_data,
            message="체크리스트가 성공적으로 업데이트되었습니다!",
            status_code=200,
        )

    except Exception as e:
        logger.error("체크리스트 업데이트 중 오류 발생", exc_info=True)
        return error_json_response("체크리스트 업데이트 실패", status_code=500)


@tasks_bp.route("/irregular_tasks", methods=["GET"])
def get_irregular_tasks():
    """
    비정기 업무 체크리스트 조회 API (가장 최근 상태만 반환)
    ---
    tags:
      - Irregular Tasks
    summary: "비정기 업무 체크리스트의 가장 최근 상태를 조회합니다."
    responses:
      200:
        description: 비정기 업무 체크리스트 조회 성공
      500:
        description: 비정기 업무 조회 실패
    """
    try:
        session = get_db_session()

        # 비정기 업무는 UncheckedDescription 모델을 사용
        from app.models.models import UncheckedDescription

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

        session.close()

        return json_response(
            data=tasks, message="비정기 업무 체크리스트 조회 성공", status_code=200
        )

    except Exception as e:
        logger.error("비정기 업무 조회 오류", exc_info=True)
        return error_json_response("비정기 업무 조회 실패", status_code=500)


@tasks_bp.route("/irregular_tasks", methods=["POST"])
def save_irregular_tasks():
    """
    비정기 업무 체크리스트 추가 저장 API
    기존 데이터를 덮어씌우지 않고 새로운 체크 상태를 추가
    ---
    tags:
      - Irregular Tasks
    summary: "비정기 업무 체크리스트 업데이트 데이터를 저장합니다."
    parameters:
      - in: body
        name: body
        description: "저장할 비정기 업무 체크리스트 업데이트 데이터"
        required: true
        schema:
          type: object
          properties:
            updates:
              type: array
              items:
                type: object
                properties:
                  task_name:
                    type: string
                  is_checked:
                    type: boolean
            training_course:
              type: string
    responses:
      201:
        description: 비정기 업무 체크리스트 저장 성공
      500:
        description: 비정기 업무 체크리스트 저장 실패
    """
    try:
        data = request.json
        updates = data.get("updates")
        training_course = data.get("training_course")

        if not updates or not training_course:
            return error_json_response("업데이트 데이터와 훈련 과정명이 필요합니다.", status_code=400)

        session = get_db_session()
        try:
            from app.models.models import UncheckedDescription

            for update in updates:
                task_name = update.get("task_name")
                is_checked = update.get("is_checked")

                # 비정기 업무 저장
                irregular_task = UncheckedDescription(
                    content=task_name,
                    training_course=training_course,
                    resolved=is_checked,
                )
                session.add(irregular_task)

            session.commit()

        except Exception as e:
            session.rollback()
            logger.error(f"비정기 업무 체크리스트 저장 중 오류: {str(e)}")
            return error_json_response("비정기 업무 체크리스트 저장 실패", status_code=500)
        finally:
            session.close()

        return json_response(
            data=None,
            message="비정기 업무 체크리스트가 저장되었습니다!",
            status_code=201,
        )
    except Exception as e:
        logger.error("비정기 업무 체크리스트 저장 오류", exc_info=True)
        return error_json_response("비정기 업무 체크리스트 저장 실패", status_code=500)
