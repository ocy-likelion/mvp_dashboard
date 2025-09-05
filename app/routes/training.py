from flask import Blueprint, request, jsonify
import logging

from app.serializers import (
    TrainingSerializer,
    UncheckedSerializer,
    json_response,
    error_json_response,
    handle_serialization_errors,
)
from app.services import TrainingService, UncheckedService

training_bp = Blueprint("training", __name__)
logger = logging.getLogger(__name__)


@training_bp.route("/training_courses", methods=["GET"])
def get_training_courses():
    """
    training_info 테이블에서 training_course 목록을 가져오는 API
    (현재 진행 중이거나 종료된 지 1주일 이내의 과정만 반환)
    ---
    tags:
      - Training Info
    summary: 활성 훈련 과정 목록 조회
    description: |
      현재 진행 중이거나 종료된 지 1주일 이내의 훈련 과정 목록을 조회합니다.
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/training_courses', {
        method: 'GET',
        credentials: 'include'
      });
      
      const result = await response.json();
      console.log(result);
      ```
    responses:
      200:
        description: 유효한 훈련과정 목록 반환
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "훈련 과정 목록 조회 성공"
            data:
              type: array
              items:
                type: string
              example: ["데이터 분석 스쿨 4기", "웹 개발 스쿨 3기"]
        examples:
          application/json:
            summary: 훈련 과정 목록 조회 성공 응답
            value:
              success: true
              message: "훈련 과정 목록 조회 성공"
              data: ["데이터 분석 스쿨 4기", "웹 개발 스쿨 3기"]
      500:
        description: 훈련과정 목록 불러오기 실패
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "훈련 과정 목록을 불러오는데 실패했습니다."
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 500
    """
    try:
        course_names = TrainingService.get_active_training_courses()

        return json_response(
            data=course_names, message="훈련 과정 목록 조회 성공", status_code=200
        )

    except Exception as e:
        logger.error("Error fetching training courses", exc_info=True)
        return error_json_response(
            "훈련 과정 목록을 불러오는데 실패했습니다.", status_code=500
        )


@training_bp.route("/training_info", methods=["POST"])
@handle_serialization_errors
def create_training_info():
    """
    훈련 과정 정보 생성 API
    ---
    tags:
      - Training
    summary: 새로운 훈련 과정 정보 생성
    description: |
      새로운 훈련 과정 정보를 생성합니다.
      
      ### API 명세
      **POST** `/training_info`
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/training_info', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          training_course: "데이터 분석 스쿨 5기",
          start_date: "2025-02-01",
          end_date: "2025-05-31",
          dept: "데이터사이언스팀",
          manager_name: "김매니저"
        })
      });
      
      const result = await response.json();
      console.log(result);
      ```
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - training_course
          properties:
            training_course:
              type: string
              description: 훈련 과정명
              example: "데이터 분석 스쿨 5기"
            start_date:
              type: string
              description: 시작 날짜 (YYYY-MM-DD 형식)
              example: "2025-02-01"
            end_date:
              type: string
              description: 종료 날짜 (YYYY-MM-DD 형식)
              example: "2025-05-31"
            dept:
              type: string
              description: 부서명
              example: "데이터사이언스팀"
            manager_name:
              type: string
              description: 매니저명
              example: "김매니저"
    responses:
      201:
        description: 훈련 과정 정보 생성 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "훈련 과정 정보가 성공적으로 생성되었습니다."
            data:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                training_course:
                  type: string
                  example: "데이터 분석 스쿨 5기"
                start_date:
                  type: string
                  example: "2025-02-01"
                end_date:
                  type: string
                  example: "2025-05-31"
                dept:
                  type: string
                  example: "데이터사이언스팀"
                manager_name:
                  type: string
                  example: "김매니저"
        examples:
          application/json:
            summary: 훈련 과정 정보 생성 성공 응답
            value:
              success: true
              message: "훈련 과정 정보가 성공적으로 생성되었습니다."
              data:
                id: 1
                training_course: "데이터 분석 스쿨 5기"
                start_date: "2025-02-01"
                end_date: "2025-05-31"
                dept: "데이터사이언스팀"
                manager_name: "김매니저"
    """
    try:
        validated_data = TrainingSerializer.deserialize_training_info_create(
            request.json
        )
        training_data = TrainingService.create_training_info(validated_data)

        return json_response(
            data=training_data, message="훈련 과정이 저장되었습니다!", status_code=201
        )
    except Exception as e:
        logger.error("Error saving training info", exc_info=True)
        return error_json_response("훈련 과정 저장 실패", status_code=500)


@training_bp.route("/training_info", methods=["GET"])
def get_training_info():
    """
    훈련 과정 목록 조회 API
    ---
    tags:
      - Training Info
    summary: 모든 훈련 과정 정보 조회
    description: |
      저장된 모든 훈련 과정 정보를 조회합니다.
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/training_info', {
        method: 'GET',
        credentials: 'include'
      });
      
      const result = await response.json();
      console.log(result);
      ```
    responses:
      200:
        description: 저장된 훈련 과정 목록 반환
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "훈련 과정 목록 조회 성공"
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  training_course:
                    type: string
                    example: "데이터 분석 스쿨 4기"
                  start_date:
                    type: string
                    format: date
                    example: "2025-01-02"
                  end_date:
                    type: string
                    format: date
                    example: "2025-06-01"
                  dept:
                    type: string
                    example: "TechSol"
                  manager_name:
                    type: string
                    example: "홍길동"
        examples:
          application/json:
            summary: 훈련 과정 목록 조회 성공 응답
            value:
              success: true
              message: "훈련 과정 목록 조회 성공"
              data:
                - id: 1
                  training_course: "데이터 분석 스쿨 4기"
                  start_date: "2025-01-02"
                  end_date: "2025-06-01"
                  dept: "TechSol"
                  manager_name: "홍길동"
                - id: 2
                  training_course: "웹 개발 스쿨 3기"
                  start_date: "2025-02-01"
                  end_date: "2025-07-01"
                  dept: "DevTeam"
                  manager_name: "김철수"
      500:
        description: 훈련 과정 목록 조회 실패
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "훈련 과정 목록 조회 실패"
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 500
    """
    try:
        courses_data = TrainingService.get_all_training_info()
        serialized_courses_data = TrainingSerializer.serialize_training_info(
            courses_data
        )

        return json_response(
            data=serialized_courses_data, message="훈련 과정 목록 조회 성공", status_code=200
        )

    except Exception as e:
        logger.error("Error fetching training info", exc_info=True)
        return error_json_response("훈련 과정 목록 조회 실패", status_code=500)


@training_bp.route("/unchecked_descriptions", methods=["GET"])
def get_unchecked_descriptions():
    """
    미체크 항목 설명 및 액션 플랜 조회 API (부서명 포함)
    ---
    tags:
      - Unchecked Descriptions
    summary: 미체크 항목 목록 조회
    description: |
      미체크 항목의 설명과 액션 플랜을 부서명과 함께 조회합니다.
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/unchecked_descriptions', {
        method: 'GET',
        credentials: 'include'
      });
      
      const result = await response.json();
      console.log(result);
      ```
    responses:
      200:
        description: 미체크 항목 목록 조회 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "미체크 항목 목록 조회 성공"
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  content:
                    type: string
                    example: "출석 체크 미완료"
                  action_plan:
                    type: string
                    example: "매일 출석을 체크하도록 안내"
                  training_course:
                    type: string
                    example: "데이터 분석 스쿨 4기"
                  dept:
                    type: string
                    example: "TechSol"
                  created_at:
                    type: string
                    format: date-time
                    example: "2025-01-15T10:30:00"
                  resolved:
                    type: boolean
                    example: false
                  due_days:
                    type: integer
                    example: 3
                  deadline:
                    type: string
                    format: date
                    example: "2025-01-18"
                  is_overdue:
                    type: boolean
                    example: false
        examples:
          application/json:
            summary: 미체크 항목 목록 조회 성공 응답
            value:
              success: true
              message: "미체크 항목 목록 조회 성공"
              data:
                - id: 1
                  content: "출석 체크 미완료"
                  action_plan: "매일 출석을 체크하도록 안내"
                  training_course: "데이터 분석 스쿨 4기"
                  dept: "TechSol"
                  created_at: "2025-01-15T10:30:00"
                  resolved: false
                  due_days: 3
                  deadline: "2025-01-18"
                  is_overdue: false
      500:
        description: 미체크 항목 목록 조회 실패
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "미체크 항목 목록 조회 실패"
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 500
    """
    try:
        unchecked_items = UncheckedService.get_unchecked_descriptions()
        
        return json_response(
            data=unchecked_items,
            message="미체크 항목 목록 조회 성공",
            status_code=200,
        )

    except Exception as e:
        logger.error("Error retrieving unchecked descriptions", exc_info=True)
        return error_json_response("미체크 항목 목록 조회 실패", status_code=500)


@training_bp.route("/unchecked_descriptions", methods=["POST"])
@handle_serialization_errors
def save_unchecked_description():
    """
    미체크 항목 설명과 액션 플랜 저장 API
    ---
    tags:
      - Unchecked Descriptions
    summary: 새로운 미체크 항목 저장
    description: |
      새로운 미체크 항목의 설명과 액션 플랜을 저장합니다.
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/unchecked_descriptions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          content: "출석 체크 미완료",
          action_plan: "매일 출석을 체크하도록 안내",
          training_course: "데이터 분석 스쿨 4기"
        })
      });
      
      const result = await response.json();
      console.log(result);
      ```
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - content
            - action_plan
            - training_course
          properties:
            content:
              type: string
              description: 미체크 항목 내용
              example: "출석 체크 미완료"
            action_plan:
              type: string
              description: 액션 플랜
              example: "매일 출석을 체크하도록 안내"
            training_course:
              type: string
              description: 훈련 과정명
              example: "데이터 분석 스쿨 4기"
    responses:
      201:
        description: 미체크 항목과 액션 플랜이 성공적으로 저장됨
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "미체크 항목과 액션 플랜이 저장되었습니다!"
            data:
              type: null
              example: null
        examples:
          application/json:
            summary: 미체크 항목 저장 성공 응답
            value:
              success: true
              message: "미체크 항목과 액션 플랜이 저장되었습니다!"
              data: null
      400:
        description: 필수 데이터 누락
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "필수 데이터가 누락되었습니다."
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 400
      500:
        description: 서버 오류 발생
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "미체크 항목 저장 실패"
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 500
    """
    try:
        validated_data = UncheckedSerializer.deserialize_unchecked_description_create(
            request.json
        )
        UncheckedService.create_unchecked_description(validated_data)

        return json_response(
            data=None,
            message="미체크 항목과 액션 플랜이 저장되었습니다!",
            status_code=201,
        )

    except Exception as e:
        logger.error("Error saving unchecked description", exc_info=True)
        return error_json_response("미체크 항목 저장 실패", status_code=500)


@training_bp.route("/unchecked_comments", methods=["POST"])
@handle_serialization_errors
def add_unchecked_comment():
    """
    미체크 항목에 댓글 추가 API
    ---
    tags:
      - Unchecked Comments
    summary: 미체크 항목에 댓글 추가
    description: |
      특정 미체크 항목에 댓글을 추가합니다.
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/unchecked_comments', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          unchecked_id: 1,
          comment: "이 문제를 해결하기 위해 추가 조치가 필요합니다."
        })
      });
      
      const result = await response.json();
      console.log(result);
      ```
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - unchecked_id
            - comment
          properties:
            unchecked_id:
              type: integer
              description: 미체크 항목 ID
              example: 1
            comment:
              type: string
              description: 댓글 내용
              example: "이 문제를 해결하기 위해 추가 조치가 필요합니다."
    responses:
      201:
        description: 댓글 저장 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "댓글이 저장되었습니다."
            data:
              type: null
              example: null
        examples:
          application/json:
            summary: 댓글 저장 성공 응답
            value:
              success: true
              message: "댓글이 저장되었습니다."
              data: null
      400:
        description: 요청 데이터 오류
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "요청 데이터가 올바르지 않습니다."
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 400
      500:
        description: 서버 오류 발생
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "댓글 저장 실패"
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 500
    """
    try:
        validated_data = UncheckedSerializer.deserialize_unchecked_comment_create(
            request.json
        )
        UncheckedService.add_unchecked_comment(validated_data)

        return json_response(
            data=None, message="댓글이 저장되었습니다.", status_code=201
        )
    except Exception as e:
        logger.error("Error saving unchecked comment", exc_info=True)
        return error_json_response("댓글 저장 실패", status_code=500)


@training_bp.route("/unchecked_descriptions/resolve", methods=["POST"])
@handle_serialization_errors
def resolve_unchecked_description():
    """
    미체크 항목 해결 API
    ---
    tags:
      - Unchecked Descriptions
    summary: 미체크 항목 해결 처리
    description: |
      특정 미체크 항목을 해결된 상태로 변경합니다.
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/unchecked_descriptions/resolve', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          unchecked_id: 1
        })
      });
      
      const result = await response.json();
      console.log(result);
      ```
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - unchecked_id
          properties:
            unchecked_id:
              type: integer
              description: 해결할 미체크 항목 ID
              example: 1
    responses:
      200:
        description: 미체크 항목 해결 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "미체크 항목이 해결되었습니다."
            data:
              type: null
              example: null
        examples:
          application/json:
            summary: 미체크 항목 해결 성공 응답
            value:
              success: true
              message: "미체크 항목이 해결되었습니다."
              data: null
      400:
        description: 요청 데이터 오류
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "요청 데이터가 올바르지 않습니다."
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 400
      500:
        description: 서버 오류 발생
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "미체크 항목 해결 실패"
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 500
    """
    try:
        validated_data = UncheckedSerializer.deserialize_unchecked_resolve(request.json)
        UncheckedService.resolve_unchecked_description(validated_data)

        return jsonify({"success": True, "message": "미체크 항목이 해결되었습니다."}), 200
    except Exception as e:
        logger.error("Error resolving unchecked description", exc_info=True)
        return error_json_response("미체크 항목 해결 실패", status_code=500)


@training_bp.route("/unchecked_comments", methods=["GET"])
def get_unchecked_comments():
    """
    미체크 항목의 댓글 조회 API
    ---
    tags:
      - Unchecked Comments
    summary: 미체크 항목의 댓글 목록 조회
    description: |
      특정 미체크 항목의 댓글 목록을 조회합니다.
      
      ### 사용 예시
      ```javascript
      const response = await fetch('/unchecked_comments?unchecked_id=1', {
        method: 'GET',
        credentials: 'include'
      });
      
      const result = await response.json();
      console.log(result);
      ```
    parameters:
      - name: unchecked_id
        in: query
        type: integer
        required: true
        description: "조회할 미체크 항목 ID"
        example: 1
    responses:
      200:
        description: 미체크 항목의 댓글 목록 반환
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "미체크 항목 댓글 조회 성공"
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  comment:
                    type: string
                    example: "이 문제를 해결하기 위해 추가 조치가 필요합니다."
                  created_at:
                    type: string
                    format: date-time
                    example: "2025-01-15T10:30:00"
                  unchecked_id:
                    type: integer
                    example: 1
        examples:
          application/json:
            summary: 댓글 목록 조회 성공 응답
            value:
              success: true
              message: "미체크 항목 댓글 조회 성공"
              data:
                - id: 1
                  comment: "이 문제를 해결하기 위해 추가 조치가 필요합니다."
                  created_at: "2025-01-15T10:30:00"
                  unchecked_id: 1
                - id: 2
                  comment: "관련 부서에 문의하여 해결 방안을 모색하겠습니다."
                  created_at: "2025-01-15T11:00:00"
                  unchecked_id: 1
      400:
        description: "미체크 항목 ID 누락"
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "미체크 항목 ID가 누락되었습니다."
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 400
      500:
        description: "댓글 조회 실패"
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "미체크 항목 댓글 조회 실패"
            details:
              type: object
              example: null
            status_code:
              type: integer
              example: 500
    """
    try:
        validated_data = UncheckedSerializer.deserialize_unchecked_comment_get(request.args)
        comments = UncheckedService.get_unchecked_comments(validated_data)
        serialized_comments = UncheckedSerializer.serialize_unchecked_comments(comments)

        return json_response(
            data=serialized_comments, message="미체크 항목 댓글 조회 성공", status_code=200
        )

    except Exception as e:
        logger.error("Error retrieving unchecked comments", exc_info=True)
        return error_json_response("미체크 항목 댓글 조회 실패", status_code=500)
