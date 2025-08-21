from flask import Blueprint, request
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
    responses:
      200:
        description: 유효한 훈련과정 목록 반환
      500:
        description: 훈련과정 목록 불러오기 실패
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
def save_training_info():
    """
    훈련 과정 정보 저장 API
    ---
    tags:
      - Training Info
    parameters:
      - in: body
        name: body
        description: "훈련 과정 정보를 JSON 형식으로 전달"
        required: true
        schema:
          type: object
          required:
            - training_course
            - start_date
            - end_date
            - dept
            - manager_name
          properties:
            training_course:
              type: string
              example: "데이터 분석 스쿨 100기"
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
    responses:
      201:
        description: 훈련 과정 저장 성공
      400:
        description: 필수 필드 누락
      500:
        description: 훈련 과정 저장 실패
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
    responses:
      200:
        description: 저장된 훈련 과정 목록 반환
      500:
        description: 훈련 과정 목록 조회 실패
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
    responses:
      200:
        description: 미체크 항목 목록 조회 성공
      500:
        description: 미체크 항목 목록 조회 실패
    """
    try:
        unchecked_items = UncheckedService.get_unchecked_descriptions()
        serialized_unchecked_items = UncheckedSerializer.serialize_unchecked_descriptions(unchecked_items)
        
        return json_response(
            data=serialized_unchecked_items,
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
            action_plan:
              type: string
            training_course:
              type: string
    responses:
      201:
        description: 미체크 항목과 액션 플랜이 성공적으로 저장됨
      400:
        description: 필수 데이터 누락
      500:
        description: 서버 오류 발생
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
            comment:
              type: string
    responses:
      201:
        description: 댓글 저장 성공
      400:
        description: 요청 데이터 오류
      500:
        description: 서버 오류 발생
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
    responses:
      200:
        description: 미체크 항목 해결 성공
      400:
        description: 요청 데이터 오류
      500:
        description: 서버 오류 발생
    """
    try:
        validated_data = UncheckedSerializer.deserialize_unchecked_resolve(request.json)
        UncheckedService.resolve_unchecked_description(validated_data)

        return json_response(
            data=None, message="미체크 항목이 해결되었습니다.", status_code=200
        )
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
    parameters:
      - name: unchecked_id
        in: query
        type: integer
        required: true
        description: "조회할 미체크 항목 ID"
    responses:
      200:
        description: 미체크 항목의 댓글 목록 반환
      400:
        description: "미체크 항목 ID 누락"
      500:
        description: "댓글 조회 실패"
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
