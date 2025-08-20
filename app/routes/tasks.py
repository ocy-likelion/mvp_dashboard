from flask import Blueprint, request
import logging
from app.models.db import get_db_session
from app.serializers import (
    TaskSerializer,
    UncheckedSerializer,
    json_response,
    error_json_response,
    handle_serialization_errors,
)
from app.services import TaskService, UncheckedService

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

        # Service를 사용한 업무 체크리스트 조회
        tasks = TaskService.get_tasks(session, task_category)
        # Serializer로 데이터 직렬화
        serialized_tasks = TaskSerializer.serialize_task_items(tasks)

        session.close()

        return json_response(
            data=serialized_tasks, message="업무 체크리스트 조회 성공", status_code=200
        )
    except Exception as e:
        logger.error("Error retrieving tasks", exc_info=True)
        return error_json_response("업무 체크리스트 조회 실패", status_code=500)


@tasks_bp.route("/tasks", methods=["POST"])
@handle_serialization_errors
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
        if not data:
            return error_json_response("요청 데이터가 없습니다.", status_code=400)

        session = get_db_session()
        try:
            # 데이터 검증
            validated_data = TaskSerializer.deserialize_task_update(data)
            # Service를 사용한 체크리스트 저장/업데이트
            TaskService.save_task_checklist(session, validated_data)
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
@handle_serialization_errors
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
        if not data:
            return error_json_response("요청 데이터가 없습니다.", status_code=400)

        session = get_db_session()
        try:
            # 데이터 검증
            validated_data = TaskSerializer.deserialize_task_update(data)
            # Service를 사용한 체크리스트 업데이트
            result = TaskService.update_task_checklist(session, validated_data)
            # Serializer를 사용한 응답 데이터 구성
            response_data = TaskSerializer.serialize_task_update_result(result)
            session.commit()

        except ValueError as e:
            session.rollback()
            # 비즈니스 규칙 위반 (404 에러)
            return error_json_response(str(e), status_code=404)
        except Exception as e:
            session.rollback()
            logger.error(f"체크리스트 업데이트 중 오류: {str(e)}")
            return error_json_response("체크리스트 업데이트 실패", status_code=500)
        finally:
            session.close()

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

        # Service를 사용한 비정기 업무 조회
        tasks = UncheckedService.get_irregular_tasks(session)

        session.close()

        return json_response(
            data=tasks, message="비정기 업무 체크리스트 조회 성공", status_code=200
        )

    except Exception as e:
        logger.error("비정기 업무 조회 오류", exc_info=True)
        return error_json_response("비정기 업무 조회 실패", status_code=500)


@tasks_bp.route("/irregular_tasks", methods=["POST"])
@handle_serialization_errors
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
        if not data:
            return error_json_response("요청 데이터가 없습니다.", status_code=400)

        session = get_db_session()
        try:
            # 데이터 검증
            validated_data = UncheckedSerializer.deserialize_irregular_task_create(data)
            # Service를 사용한 비정기 업무 저장
            UncheckedService.save_irregular_tasks(session, validated_data)
            session.commit()

        except Exception as e:
            session.rollback()
            logger.error(f"비정기 업무 체크리스트 저장 중 오류: {str(e)}")
            return error_json_response(
                "비정기 업무 체크리스트 저장 실패", status_code=500
            )
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
