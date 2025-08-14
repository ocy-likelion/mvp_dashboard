from flask import Blueprint, request, jsonify
import logging
from app.models.db import get_db_session
from app.models.models import (
    TrainingInfo,
    UncheckedDescription,
    UncheckedComment,
    TaskItem,
)
from datetime import datetime, timedelta

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
        session = get_db_session()

        # 현재 날짜 기준으로 종료된 지 1주일 이내이거나 아직 진행 중인 과정만 조회
        one_week_ago = datetime.now().date() - timedelta(days=7)
        courses_query = (
            session.query(TrainingInfo)
            .filter(TrainingInfo.end_date >= one_week_ago)
            .order_by(TrainingInfo.start_date.desc())
        )

        courses = [course.training_course for course in courses_query.all()]

        session.close()

        return jsonify({"success": True, "data": courses}), 200

    except Exception as e:
        logger.error("Error fetching training courses", exc_info=True)
        return (
            jsonify(
                {
                    "success": False,
                    "message": "훈련 과정 목록을 불러오는데 실패했습니다.",
                }
            ),
            500,
        )


@training_bp.route("/training_info", methods=["POST"])
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
        data = request.json
        training_course = data.get("training_course", "").strip()
        start_date = data.get("start_date", "").strip()
        end_date = data.get("end_date", "").strip()
        dept = data.get("dept", "").strip()
        manager_name = data.get("manager_name", "").strip()

        if (
            not training_course
            or not start_date
            or not end_date
            or not dept
            or not manager_name
        ):
            return (
                jsonify({"success": False, "message": "모든 필드를 입력하세요."}),
                400,
            )

        session = get_db_session()
        try:
            # 날짜 문자열을 Date 객체로 변환
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

            training_info = TrainingInfo(
                training_course=training_course,
                start_date=start_date_obj,
                end_date=end_date_obj,
                dept=dept,
                manager_name=manager_name,
            )

            session.add(training_info)
            session.commit()

        except Exception as e:
            session.rollback()
            logger.error(f"훈련 과정 저장 중 오류: {str(e)}")
            return (
                jsonify({"success": False, "message": "Failed to save training info"}),
                500,
            )
        finally:
            session.close()

        return jsonify({"success": True, "message": "훈련 과정이 저장되었습니다!"}), 201
    except Exception as e:
        logger.error("Error saving training info", exc_info=True)
        return (
            jsonify({"success": False, "message": "Failed to save training info"}),
            500,
        )


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
        session = get_db_session()

        courses_query = session.query(TrainingInfo).order_by(
            TrainingInfo.start_date.desc()
        )
        courses = courses_query.all()

        courses_data = [
            {
                "training_course": course.training_course,
                "start_date": (
                    course.start_date.strftime("%Y-%m-%d")
                    if course.start_date
                    else None
                ),
                "end_date": (
                    course.end_date.strftime("%Y-%m-%d") if course.end_date else None
                ),
                "dept": course.dept,
            }
            for course in courses
        ]

        session.close()

        return jsonify({"success": True, "data": courses_data})

    except Exception as e:
        logger.error("Error fetching training info", exc_info=True)
        return (
            jsonify({"success": False, "message": "Failed to fetch training info"}),
            500,
        )


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
        session = get_db_session()

        # 미체크 항목 조회 (resolved=False인 항목들)
        unchecked_query = (
            session.query(UncheckedDescription)
            .filter(UncheckedDescription.resolved == False)
            .order_by(UncheckedDescription.created_at.desc())
        )

        unchecked_items = []
        for item in unchecked_query.all():
            # 부서 정보 조회
            training_info = (
                session.query(TrainingInfo)
                .filter(TrainingInfo.training_course == item.training_course)
                .first()
            )
            dept = training_info.dept if training_info else None

            # due days 조회 (task_items에서 매칭되는 항목 찾기)
            due_days = 3  # 기본값
            if item.content:
                task_item = (
                    session.query(TaskItem)
                    .filter(
                        TaskItem.task_name.in_(
                            [
                                task_name
                                for task_name in session.query(TaskItem.task_name).all()
                            ]
                        )
                    )
                    .filter(
                        item.content.like(f"%{TaskItem.task_name}%에 대한 미체크 사유")
                    )
                    .first()
                )
                if task_item:
                    due_days = task_item.due or 3

            # 마감일 계산
            deadline = item.created_at.date() + timedelta(days=due_days)
            is_overdue = datetime.now().date() > deadline

            unchecked_items.append(
                {
                    "id": item.id,
                    "content": item.content,
                    "action_plan": item.action_plan,
                    "training_course": item.training_course,
                    "dept": dept,
                    "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "resolved": item.resolved,
                    "due_days": due_days,
                    "deadline": deadline.strftime("%Y-%m-%d"),
                    "is_overdue": is_overdue,
                }
            )

        session.close()

        return jsonify({"success": True, "data": unchecked_items}), 200

    except Exception as e:
        logger.error("Error retrieving unchecked descriptions", exc_info=True)
        return (
            jsonify(
                {
                    "success": False,
                    "message": "미체크 항목 목록을 불러오는 중 오류 발생",
                }
            ),
            500,
        )


@training_bp.route("/unchecked_descriptions", methods=["POST"])
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
            - description
            - action_plan
            - training_course
          properties:
            description:
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
        if not request.is_json:
            return jsonify({"success": False, "message": "Invalid JSON format"}), 400

        data = request.get_json()
        description = data.get("description", "").strip()
        action_plan = data.get("action_plan", "").strip()
        training_course = data.get("training_course", "").strip()

        if not description or not action_plan or not training_course:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "설명, 액션 플랜, 훈련과정명을 모두 입력하세요.",
                    }
                ),
                400,
            )

        session = get_db_session()
        try:
            unchecked_description = UncheckedDescription(
                content=description,
                action_plan=action_plan,
                training_course=training_course,
                resolved=False,
            )

            session.add(unchecked_description)
            session.commit()

        except Exception as e:
            session.rollback()
            logger.error(f"미체크 항목 저장 중 오류: {str(e)}")
            return jsonify({"success": False, "message": "서버 오류 발생"}), 500
        finally:
            session.close()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "미체크 항목과 액션 플랜이 저장되었습니다!",
                }
            ),
            201,
        )

    except Exception as e:
        logger.error("Error saving unchecked description", exc_info=True)
        return jsonify({"success": False, "message": "서버 오류 발생"}), 500


@training_bp.route("/unchecked_comments", methods=["POST"])
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
        data = request.json
        unchecked_id = data.get("unchecked_id")
        comment = data.get("comment")

        if not unchecked_id or not comment:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "미체크 항목 ID와 댓글 내용을 입력하세요.",
                    }
                ),
                400,
            )

        session = get_db_session()
        try:
            unchecked_comment = UncheckedComment(
                unchecked_id=unchecked_id,
                comment=comment,
            )

            session.add(unchecked_comment)
            session.commit()

        except Exception as e:
            session.rollback()
            logger.error(f"댓글 저장 중 오류: {str(e)}")
            return jsonify({"success": False, "message": "댓글 저장 실패"}), 500
        finally:
            session.close()

        return jsonify({"success": True, "message": "댓글이 저장되었습니다."}), 201
    except Exception as e:
        logger.error("Error saving unchecked comment", exc_info=True)
        return jsonify({"success": False, "message": "댓글 저장 실패"}), 500


@training_bp.route("/unchecked_descriptions/resolve", methods=["POST"])
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
        data = request.json
        unchecked_id = data.get("unchecked_id")

        if not unchecked_id:
            return (
                jsonify({"success": False, "message": "미체크 항목 ID가 필요합니다."}),
                400,
            )

        session = get_db_session()
        try:
            unchecked_item = (
                session.query(UncheckedDescription)
                .filter(UncheckedDescription.id == unchecked_id)
                .first()
            )

            if not unchecked_item:
                return (
                    jsonify(
                        {"success": False, "message": "미체크 항목을 찾을 수 없습니다."}
                    ),
                    404,
                )

            unchecked_item.resolved = True
            session.commit()

        except Exception as e:
            session.rollback()
            logger.error(f"미체크 항목 해결 중 오류: {str(e)}")
            return jsonify({"success": False, "message": "미체크 항목 해결 실패"}), 500
        finally:
            session.close()

        return (
            jsonify({"success": True, "message": "미체크 항목이 해결되었습니다."}),
            200,
        )
    except Exception as e:
        logger.error("Error resolving unchecked description", exc_info=True)
        return jsonify({"success": False, "message": "미체크 항목 해결 실패"}), 500


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
        unchecked_id = request.args.get("unchecked_id")

        if not unchecked_id:
            return (
                jsonify({"success": False, "message": "미체크 항목 ID를 입력하세요."}),
                400,
            )

        session = get_db_session()
        try:
            comments_query = (
                session.query(UncheckedComment)
                .filter(UncheckedComment.unchecked_id == unchecked_id)
                .order_by(UncheckedComment.created_at.asc())
            )

            comments = [
                {
                    "id": comment.id,
                    "comment": comment.comment,
                    "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for comment in comments_query.all()
            ]

            return jsonify({"success": True, "data": comments}), 200

        finally:
            session.close()

    except Exception as e:
        logger.error("Error retrieving unchecked comments", exc_info=True)
        return jsonify({"success": False, "message": "미체크 항목 댓글 조회 실패"}), 500
