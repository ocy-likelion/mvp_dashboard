from flask import Blueprint, request
import logging
from app.serializers import (
    AdminSerializer,
    json_response,
    error_json_response,
)
from app.services import AdminService

admin_bp = Blueprint("admin", __name__)
logger = logging.getLogger(__name__)


@admin_bp.route("/admin/task_status", methods=["GET"])
def get_task_status():
    """
    훈련 과정별 업무 체크리스트 체크율 조회 API
    ---
    tags:
      - Admin
    summary: 훈련 과정별 업무 체크 상태 조회
    description: |
      특정 날짜의 훈련 과정별 업무 체크리스트 체크율을 조회합니다.
      
      ### 사용 예시
      ```javascript
      // 당일 체크율 조회
      const response = await fetch('/admin/task_status', {
        method: 'GET',
        credentials: 'include'
      });
      
      // 특정 날짜 체크율 조회
      const response = await fetch('/admin/task_status?date=2025-01-15', {
        method: 'GET',
        credentials: 'include'
      });
      
      const result = await response.json();
      console.log(result);
      ```
    parameters:
      - name: date
        in: query
        description: 조회할 날짜 (YYYY-MM-DD 형식, 기본값은 당일)
        required: false
        type: string
        example: "2025-01-15"
    responses:
      200:
        description: 훈련 과정별 체크율 데이터를 반환
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "업무 체크 상태 조회 성공"
            data:
              type: object
              properties:
                task_status:
                  type: array
                  items:
                    type: object
                    properties:
                      training_course:
                        type: string
                        example: "데이터 분석 스쿨 4기"
                      dept:
                        type: string
                        example: "TechSol"
                      check_rate:
                        type: string
                        example: "80.0%"
                total_courses:
                  type: integer
                  example: 5
                timestamp:
                  type: string
                  format: date-time
                  example: "2025-01-15T10:30:00"
        examples:
          application/json:
            summary: 체크율 조회 성공 응답
            value:
              success: true
              message: "업무 체크 상태 조회 성공"
              data:
                task_status:
                  - training_course: "데이터 분석 스쿨 4기"
                    dept: "TechSol"
                    check_rate: "80.0%"
                  - training_course: "웹 개발 스쿨 3기"
                    dept: "DevTeam"
                    check_rate: "83.3%"
                total_courses: 2
                timestamp: "2025-01-15T10:30:00"
      400:
        description: 잘못된 날짜 형식
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "잘못된 날짜 형식입니다. YYYY-MM-DD 형식으로 입력해주세요."
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 400
      500:
        description: 체크 상태 조회 실패
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "업무 체크 상태 조회 실패"
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 500
    """
    try:
        # 간단한 파라미터 처리 (직렬화 오류 방지)
        date_param = request.args.get("date")
        validated_data = {"date": date_param} if date_param else {}
        
        task_status = AdminService.get_daily_task_status(validated_data)

        return json_response(
            data=task_status, message="업무 체크 상태 조회 성공", status_code=200
        )

    except ValueError as e:
        return error_json_response(str(e), status_code=400)

    except Exception as e:
        logger.error("업무 체크 상태 조회 중 오류 발생", exc_info=True)
        return error_json_response("업무 체크 상태 조회 실패", status_code=500)


@admin_bp.route("/admin/task_status_overall", methods=["GET"])
def get_overall_task_status():
    """
    훈련 과정별 전체 체크율 조회 API
    ---
    tags:
      - Admin
    summary: 훈련 과정별 전체 체크율 조회
    description: |
      모든 훈련 과정의 전체 체크율을 조회합니다.
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/admin/task_status_overall', {
        method: 'GET',
        credentials: 'include'
      });
      
      const result = await response.json();
      console.log(result);
      ```
    responses:
      200:
        description: 훈련 과정별 전체 체크율 데이터 반환
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "전체 업무 체크 상태 조회 성공"
            data:
              type: array
              items:
                type: object
                properties:
                  training_course:
                    type: string
                    example: "데이터 분석 스쿨 4기"
                  dept:
                    type: string
                    example: "TechSol"
                  check_rate:
                    type: string
                    example: "80.0%"
        examples:
          application/json:
            summary: 전체 체크율 조회 성공 응답
            value:
              success: true
              message: "전체 업무 체크 상태 조회 성공"
              data:
                - training_course: "데이터 분석 스쿨 4기"
                  dept: "TechSol"
                  check_rate: "80.0%"
                - training_course: "웹 개발 스쿨 3기"
                  dept: "DevTeam"
                  check_rate: "90.0%"
      500:
        description: 체크율 조회 실패
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "전체 업무 체크 상태 조회 실패"
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 500
    """
    try:
        task_status = AdminService.get_overall_task_status()

        return json_response(
            data=task_status, message="전체 업무 체크 상태 조회 성공", status_code=200
        )
    except Exception as e:
        logger.error("Error retrieving overall task status", exc_info=True)
        return error_json_response("전체 업무 체크 상태 조회 실패", status_code=500)


@admin_bp.route("/admin/task_status_combined", methods=["GET"])
def get_combined_task_status():
    """
    훈련 과정별 통합 체크율 조회 API
    ---
    tags:
      - Admin
    summary: 훈련 과정별 업무 체크율 조회 (당일, 전날, 전체)
    description: |
      각 훈련 과정별로 담당자, 당일 체크율, 전날 체크율, 전체 체크율을 조회합니다.
      종료된 지 1주일 이내의 과정만 포함됩니다.
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/admin/task_status_combined', {
        method: 'GET',
        credentials: 'include'
      });
      
      const result = await response.json();
      console.log(result);
      ```
    responses:
      200:
        description: 훈련 과정별 체크율 데이터 반환
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "통합 업무 체크 상태 조회 성공"
            data:
              type: array
              items:
                type: object
                properties:
                  training_course:
                    type: string
                    example: "데이터 분석 스쿨 4기"
                  dept:
                    type: string
                    example: "TechSol"
                  manager_name:
                    type: string
                    example: "홍길동"
                  daily_check_rate:
                    type: string
                    example: "80.0%"
                  yesterday_check_rate:
                    type: string
                    example: "75.0%"
                  overall_check_rate:
                    type: string
                    example: "78.5%"
        examples:
          application/json:
            summary: 통합 체크율 조회 성공 응답
            value:
              success: true
              message: "통합 업무 체크 상태 조회 성공"
              data:
                - training_course: "데이터 분석 스쿨 4기"
                  dept: "TechSol"
                  manager_name: "홍길동"
                  daily_check_rate: "80.0%"
                  yesterday_check_rate: "75.0%"
                  overall_check_rate: "78.5%"
                - training_course: "웹 개발 스쿨 3기"
                  dept: "DevTeam"
                  manager_name: "김철수"
                  daily_check_rate: "90.0%"
                  yesterday_check_rate: "85.0%"
                  overall_check_rate: "87.5%"
      500:
        description: 체크 상태 조회 실패
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "통합 업무 체크 상태 조회 실패"
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 500
    """
    try:
        task_status = AdminService.get_combined_task_status()
        serialized_task_status = AdminSerializer.serialize_task_status(task_status)

        return json_response(
            data=serialized_task_status, message="통합 업무 체크 상태 조회 성공", status_code=200
        )
    except Exception as e:
        logger.error("Error retrieving combined task status", exc_info=True)
        return error_json_response("통합 업무 체크 상태 조회 실패", status_code=500)
