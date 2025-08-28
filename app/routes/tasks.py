from flask import Blueprint, request
import logging
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
    description: |
      업무 체크리스트 데이터를 조회합니다. 카테고리별 필터링이 가능합니다.
      
      ### 사용 예시
      ```javascript
      // 모든 업무 체크리스트 조회
      const response = await fetch('/tasks', {
        method: 'GET',
        credentials: 'include'
      });
      
      // 특정 카테고리의 업무 체크리스트 조회
      const response = await fetch('/tasks?task_category=개발', {
        method: 'GET',
        credentials: 'include'
      });
      
      const result = await response.json();
      console.log(result);
      ```
    parameters:
      - name: task_category
        in: query
        type: string
        required: false
        description: "업무 체크리스트의 카테고리 (예: 개발, 디자인)"
        example: "개발"
    responses:
      200:
        description: 모든 업무 체크리스트 데이터를 반환함
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "업무 체크리스트 조회 성공"
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  task_name:
                    type: string
                    example: "출석 체크"
                  task_category:
                    type: string
                    example: "일반"
                  task_period:
                    type: string
                    example: "일일"
                  guide:
                    type: string
                    example: "매일 출석을 체크합니다"
                  due:
                    type: integer
                    example: 1
        examples:
          application/json:
            summary: 업무 체크리스트 조회 성공 응답
            value:
              success: true
              message: "업무 체크리스트 조회 성공"
              data:
                - id: 1
                  task_name: "출석 체크"
                  task_category: "일반"
                  task_period: "일일"
                  guide: "매일 출석을 체크합니다"
                  due: 1
                - id: 2
                  task_name: "과제 제출"
                  task_category: "개발"
                  task_period: "주간"
                  guide: "주간 과제를 제출합니다"
                  due: 7
      500:
        description: 서버 오류로 인해 업무 체크리스트 조회 실패
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "업무 체크리스트 조회 실패"
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 500
    """
    try:
        query_params = {"task_category": request.args.get("task_category")}
        validated_data = TaskSerializer.deserialize_task_filter(query_params)
        tasks_data = TaskService.get_tasks(validated_data)

        return json_response(
            data=tasks_data, message="업무 체크리스트 조회 성공", status_code=200
        )
    except Exception as e:
        logger.error("Error retrieving tasks", exc_info=True)
        return error_json_response("업무 체크리스트 조회 실패", status_code=500)


@tasks_bp.route("/tasks", methods=["POST"])
@handle_serialization_errors
def save_tasks():
    """
    업무 체크리스트 저장 API
    ---
    tags:
      - Tasks
    summary: 업무 체크리스트 저장 (동일 날짜 데이터는 업데이트)
    description: |
      업무 체크리스트를 저장합니다. 동일한 날짜의 데이터가 있으면 업데이트됩니다.
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          updates: [
            {
              task_name: "출석 체크",
              is_checked: true
            },
            {
              task_name: "과제 제출",
              is_checked: false
            }
          ],
          training_course: "데이터 분석 스쿨 4기",
          username: "홍길동"
        })
      });
      
      const result = await response.json();
      console.log(result);
      ```
    parameters:
      - in: body
        name: body
        description: 저장할 체크리스트 업데이트 데이터
        required: true
        schema:
          type: object
          required:
            - updates
            - training_course
            - username
          properties:
            updates:
              type: array
              description: 체크리스트 업데이트 항목들
              items:
                type: object
                required:
                  - task_name
                  - is_checked
                properties:
                  task_name:
                    type: string
                    description: 업무 항목명
                    example: "출석 체크"
                  is_checked:
                    type: boolean
                    description: 체크 여부
                    example: true
            training_course:
              type: string
              description: 훈련 과정명
              example: "데이터 분석 스쿨 4기"
            username:
              type: string
              description: 사용자명
              example: "홍길동"
    responses:
      201:
        description: 업무 체크리스트 저장/업데이트 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "체크리스트가 성공적으로 저장/업데이트되었습니다!"
            data:
              type: null
              example: null
        examples:
          application/json:
            summary: 체크리스트 저장 성공 응답
            value:
              success: true
              message: "체크리스트가 성공적으로 저장/업데이트되었습니다!"
              data: null
      400:
        description: 요청 데이터 없음
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "요청 데이터가 없습니다."
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 400
      500:
        description: 업무 체크리스트 저장 실패
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "체크리스트 저장 실패"
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 500
    """
    try:
        validated_data = TaskSerializer.deserialize_task_update(request.json)
        TaskService.save_task_checklist(validated_data)

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
    summary: 당일 저장된 체크리스트를 업데이트합니다
    description: |
      당일 저장된 체크리스트를 업데이트합니다. 기존 데이터가 없으면 404 에러가 발생합니다.
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/tasks/update', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          updates: [
            {
              task_name: "출석 체크",
              is_checked: true
            },
            {
              task_name: "과제 제출",
              is_checked: true
            }
          ],
          training_course: "데이터 분석 스쿨 4기"
        })
      });
      
      const result = await response.json();
      console.log(result);
      ```
    parameters:
      - in: body
        name: body
        description: 업데이트할 체크리스트 데이터
        required: true
        schema:
          type: object
          required:
            - updates
            - training_course
          properties:
            updates:
              type: array
              description: 체크리스트 업데이트 항목들
              items:
                type: object
                required:
                  - task_name
                  - is_checked
                properties:
                  task_name:
                    type: string
                    example: "출석 체크"
                    description: 업무 항목명
                  is_checked:
                    type: boolean
                    example: true
                    description: 체크 여부
            training_course:
              type: string
              example: "데이터 분석 스쿨 4기"
              description: 훈련 과정명
    responses:
      200:
        description: 체크리스트 업데이트 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "체크리스트가 성공적으로 업데이트되었습니다!"
            data:
              type: object
              properties:
                updated_count:
                  type: integer
                  example: 2
                training_course:
                  type: string
                  example: "데이터 분석 스쿨 4기"
        examples:
          application/json:
            summary: 체크리스트 업데이트 성공 응답
            value:
              success: true
              message: "체크리스트가 성공적으로 업데이트되었습니다!"
              data:
                updated_count: 2
                training_course: "데이터 분석 스쿨 4기"
      404:
        description: 업데이트할 체크리스트가 존재하지 않음
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "업데이트할 체크리스트가 존재하지 않습니다."
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 404
      500:
        description: 업데이트 실패
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "체크리스트 업데이트 실패"
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 500
    """
    try:
        try:
            validated_data = TaskSerializer.deserialize_task_update(request.json)
            result = TaskService.update_task_checklist(validated_data)
            response_data = TaskSerializer.serialize_task_update_result(result)

        except ValueError as e:
            # 비즈니스 규칙 위반 (404 에러)
            return error_json_response(str(e), status_code=404)

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
    비정기 업무 체크리스트 조회 API
    ---
    tags:
      - Irregular Tasks
    summary: 비정기 업무 체크리스트의 가장 최근 상태를 조회합니다
    description: |
      비정기 업무 체크리스트의 가장 최근 상태를 조회합니다.
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/irregular_tasks', {
        method: 'GET',
        credentials: 'include'
      });
      
      const result = await response.json();
      console.log(result);
      ```
    responses:
      200:
        description: 비정기 업무 체크리스트 조회 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "비정기 업무 체크리스트 조회 성공"
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  task_name:
                    type: string
                    example: "프로젝트 발표"
                  is_checked:
                    type: boolean
                    example: false
                  training_course:
                    type: string
                    example: "데이터 분석 스쿨 4기"
                  checked_date:
                    type: string
                    format: date-time
                    example: "2025-01-15T10:30:00"
        examples:
          application/json:
            summary: 비정기 업무 체크리스트 조회 성공 응답
            value:
              success: true
              message: "비정기 업무 체크리스트 조회 성공"
              data:
                - id: 1
                  task_name: "프로젝트 발표"
                  is_checked: false
                  training_course: "데이터 분석 스쿨 4기"
                  checked_date: "2025-01-15T10:30:00"
                - id: 2
                  task_name: "포트폴리오 작성"
                  is_checked: true
                  training_course: "데이터 분석 스쿨 4기"
                  checked_date: "2025-01-14T15:20:00"
      500:
        description: 비정기 업무 조회 실패
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "비정기 업무 조회 실패"
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 500
    """
    try:
        tasks = UncheckedService.get_irregular_tasks()
        serialized_tasks = TaskSerializer.serialize_task_items(tasks)

        return json_response(
            data=serialized_tasks, message="비정기 업무 체크리스트 조회 성공", status_code=200
        )

    except Exception as e:
        logger.error("비정기 업무 조회 오류", exc_info=True)
        return error_json_response("비정기 업무 조회 실패", status_code=500)


@tasks_bp.route("/irregular_tasks", methods=["POST"])
@handle_serialization_errors
def save_irregular_tasks():
    """
    비정기 업무 체크리스트 추가 저장 API
    ---
    tags:
      - Irregular Tasks
    summary: 비정기 업무 체크리스트 업데이트 데이터를 저장합니다
    description: |
      비정기 업무 체크리스트를 저장합니다. 기존 데이터를 덮어씌우지 않고 새로운 체크 상태를 추가합니다.
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/irregular_tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          updates: [
            {
              task_name: "프로젝트 발표",
              is_checked: true
            },
            {
              task_name: "포트폴리오 작성",
              is_checked: false
            }
          ],
          training_course: "데이터 분석 스쿨 4기"
        })
      });
      
      const result = await response.json();
      console.log(result);
      ```
    parameters:
      - in: body
        name: body
        description: "저장할 비정기 업무 체크리스트 업데이트 데이터"
        required: true
        schema:
          type: object
          required:
            - updates
            - training_course
          properties:
            updates:
              type: array
              description: 비정기 업무 체크리스트 업데이트 항목들
              items:
                type: object
                properties:
                  task_name:
                    type: string
                    description: 업무 항목명
                    example: "프로젝트 발표"
                  is_checked:
                    type: boolean
                    description: 체크 여부
                    example: true
            training_course:
              type: string
              description: 훈련 과정명
              example: "데이터 분석 스쿨 4기"
    responses:
      201:
        description: 비정기 업무 체크리스트 저장 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "비정기 업무 체크리스트가 저장되었습니다!"
            data:
              type: null
              example: null
        examples:
          application/json:
            summary: 비정기 업무 체크리스트 저장 성공 응답
            value:
              success: true
              message: "비정기 업무 체크리스트가 저장되었습니다!"
              data: null
      500:
        description: 비정기 업무 체크리스트 저장 실패
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "비정기 업무 체크리스트 저장 실패"
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 500
    """
    try:
        validated_data = UncheckedSerializer.deserialize_irregular_task_create(
            request.json
        )
        UncheckedService.save_irregular_tasks(validated_data)

        return json_response(
            data=None,
            message="비정기 업무 체크리스트가 저장되었습니다!",
            status_code=201,
        )
    except Exception as e:
        logger.error("비정기 업무 체크리스트 저장 오류", exc_info=True)
        return error_json_response("비정기 업무 체크리스트 저장 실패", status_code=500)
