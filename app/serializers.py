from typing import Any, Dict, List, Optional, Tuple
from marshmallow import ValidationError, Schema
from flask import jsonify
import bcrypt
import re
from app.schemas import (
    # 단일 객체 스키마
    user_schema,
    attendance_schema,
    issue_schema,
    issue_comment_schema,
    notice_schema,
    notice_read_schema,
    task_item_schema,
    task_checklist_schema,
    unchecked_description_schema,
    unchecked_comment_schema,
    training_info_schema,
    user_last_check_schema,
    # 다중 객체 스키마
    users_schema,
    attendances_schema,
    issues_schema,
    issue_comments_schema,
    notices_schema,
    notice_reads_schema,
    task_items_schema,
    task_checklists_schema,
    unchecked_descriptions_schema,
    unchecked_comments_schema,
    training_infos_schema,
    user_last_checks_schema,
    # 생성/수정 스키마
    user_create_schema,
    user_update_schema,
    user_login_schema,
    password_change_schema,
    attendance_create_schema,
    issue_create_schema,
    issue_comment_create_schema,
    notice_create_schema,
    notice_update_schema,
    task_item_create_schema,
    task_checklist_create_schema,
    unchecked_description_create_schema,
    unchecked_comment_create_schema,
    training_info_create_schema,
    training_info_update_schema,
    user_last_check_update_schema,
    # 추가 검증용 스키마
    task_update_schema,
    irregular_task_create_schema,
    unchecked_resolve_schema,
    notice_read_create_schema,
    notice_delete_schema,
    issue_resolve_schema,
    attendance_time_schema,
    notification_query_schema,
    # 응답 스키마
    response_schema,
    error_schema,
    pagination_schema,
)


class Serializer:
    """Marshmallow 스키마를 사용한 직렬화/역직렬화 처리 클래스"""

    @staticmethod
    def serialize(obj: Any, schema: Schema, many: bool = False) -> Dict:
        """
        객체를 직렬화하여 딕셔너리로 반환

        Args:
            obj: 직렬화할 객체 또는 객체 리스트
            schema: 사용할 Marshmallow 스키마
            many: 여러 객체를 직렬화할지 여부

        Returns:
            직렬화된 딕셔너리
        """
        try:
            if many:
                return schema.dump(obj, many=True)
            else:
                return schema.dump(obj)
        except Exception as e:
            raise ValidationError(f"직렬화 중 오류가 발생했습니다: {str(e)}")

    @staticmethod
    def deserialize(data: Dict, schema: Schema, partial: bool = False) -> Dict:
        """
        딕셔너리를 역직렬화하여 검증된 데이터로 반환

        Args:
            data: 역직렬화할 딕셔너리
            schema: 사용할 Marshmallow 스키마
            partial: 부분 업데이트 허용 여부

        Returns:
            검증된 딕셔너리
        """
        try:
            return schema.load(data, partial=partial)
        except ValidationError as e:
            raise ValidationError(f"데이터 검증 실패: {e.messages}")

    @staticmethod
    def validate(data: Dict, schema: Schema) -> Dict:
        """
        데이터 검증만 수행 (역직렬화하지 않음)

        Args:
            data: 검증할 딕셔너리
            schema: 사용할 Marshmallow 스키마

        Returns:
            검증된 딕셔너리
        """
        try:
            return schema.validate(data)
        except ValidationError as e:
            raise ValidationError(f"데이터 검증 실패: {e.messages}")


class ResponseSerializer:
    """API 응답 직렬화 처리 클래스"""

    @staticmethod
    def success_response(
        data: Any = None, message: str = "성공", pagination: Optional[Dict] = None
    ) -> Dict:
        """
        성공 응답 생성

        Args:
            data: 응답 데이터
            message: 응답 메시지
            pagination: 페이지네이션 정보

        Returns:
            성공 응답 딕셔너리
        """
        response = {"success": True, "message": message, "data": data}

        if pagination:
            response["pagination"] = pagination

        return response

    @staticmethod
    def error_response(
        error: str, details: Optional[Dict] = None, status_code: int = 400
    ) -> Dict:
        """
        에러 응답 생성

        Args:
            error: 에러 메시지
            details: 상세 에러 정보
            status_code: HTTP 상태 코드

        Returns:
            에러 응답 딕셔너리
        """
        return {
            "success": False,
            "error": error,
            "details": details,
            "status_code": status_code,
        }

    @staticmethod
    def pagination_response(
        items: List[Any], page: int, per_page: int, total: int, schema: Schema
    ) -> Dict:
        """
        페이지네이션 응답 생성

        Args:
            items: 아이템 리스트
            page: 현재 페이지
            per_page: 페이지당 아이템 수
            total: 전체 아이템 수
            schema: 직렬화할 스키마

        Returns:
            페이지네이션 응답 딕셔너리
        """
        # 아이템 직렬화
        serialized_items = Serializer.serialize(items, schema, many=True)

        # 페이지네이션 정보 계산
        pages = (total + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < pages

        pagination = {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": pages,
            "has_prev": has_prev,
            "has_next": has_next,
        }

        return ResponseSerializer.success_response(
            data=serialized_items, pagination=pagination
        )


# ============================================================================
# 모델별 직렬화 함수들
# ============================================================================


class UserSerializer:
    """사용자 관련 직렬화 함수들"""

    @staticmethod
    def serialize_user(user) -> Dict:
        """단일 사용자 직렬화"""
        return Serializer.serialize(user, user_schema)

    @staticmethod
    def serialize_users(users: List) -> List[Dict]:
        """여러 사용자 직렬화"""
        return Serializer.serialize(users, users_schema, many=True)

    @staticmethod
    def deserialize_user_create(data: Dict) -> Dict:
        """사용자 생성 데이터 역직렬화"""
        return Serializer.deserialize(data, user_create_schema)

    @staticmethod
    def deserialize_user_update(data: Dict) -> Dict:
        """사용자 수정 데이터 역직렬화"""
        return Serializer.deserialize(data, user_update_schema, partial=True)

    @staticmethod
    def deserialize_user_login(data: Dict) -> Dict:
        """로그인 데이터 역직렬화"""
        return Serializer.deserialize(data, user_login_schema)

    @staticmethod
    def deserialize_password_change(data: Dict) -> Dict:
        """비밀번호 변경 데이터 역직렬화"""
        return Serializer.deserialize(data, password_change_schema)

    # 비밀번호 관련 유틸리티 함수들
    @staticmethod
    def hash_password(password: str) -> str:
        """
        비밀번호를 bcrypt로 해싱합니다.

        Args:
            password (str): 해싱할 평문 비밀번호

        Returns:
            str: 해싱된 비밀번호 (bytes를 문자열로 인코딩)
        """
        # 비밀번호를 bytes로 인코딩
        password_bytes = password.encode("utf-8")
        # bcrypt로 해싱 (기본 라운드: 12)
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
        # bytes를 문자열로 디코딩하여 반환
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        평문 비밀번호와 해싱된 비밀번호를 비교하여 검증합니다.

        Args:
            password (str): 검증할 평문 비밀번호
            hashed_password (str): 데이터베이스에 저장된 해싱된 비밀번호

        Returns:
            bool: 비밀번호가 일치하면 True, 아니면 False
        """
        try:
            # 문자열을 bytes로 인코딩
            password_bytes = password.encode("utf-8")
            hashed_bytes = hashed_password.encode("utf-8")
            # bcrypt로 검증
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            # 인코딩 오류나 기타 예외 발생 시 False 반환
            return False

    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, str]:
        """
        비밀번호 강도를 검증합니다.

        Args:
            password (str): 검증할 비밀번호

        Returns:
            Tuple[bool, str]: (유효성 여부, 오류 메시지)
        """
        if len(password) < 8:
            return False, "비밀번호는 최소 8자 이상이어야 합니다."

        if not re.search(r"[A-Z]", password):
            return False, "비밀번호는 대문자를 포함해야 합니다."

        if not re.search(r"[a-z]", password):
            return False, "비밀번호는 소문자를 포함해야 합니다."

        if not re.search(r"\d", password):
            return False, "비밀번호는 숫자를 포함해야 합니다."

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "비밀번호는 특수문자를 포함해야 합니다."

        return True, ""

    @staticmethod
    def is_hashed_password(password: str) -> bool:
        """
        비밀번호가 이미 해싱되어 있는지 확인합니다.

        Args:
            password (str): 확인할 비밀번호

        Returns:
            bool: 해싱된 비밀번호이면 True, 평문이면 False
        """
        # bcrypt 해시는 항상 $2b$로 시작하고 특정 길이를 가집니다
        return password.startswith("$2b$") and len(password) == 60


class AttendanceSerializer:
    """출석 관련 직렬화 함수들"""

    @staticmethod
    def serialize_attendance(attendance) -> Dict:
        """단일 출석 직렬화"""
        return Serializer.serialize(attendance, attendance_schema)

    @staticmethod
    def serialize_attendances(attendances: List) -> List[Dict]:
        """여러 출석 직렬화"""
        return Serializer.serialize(attendances, attendances_schema, many=True)

    @staticmethod
    def deserialize_attendance_create(data: Dict) -> Dict:
        """출석 생성 데이터 역직렬화"""
        return Serializer.deserialize(data, attendance_create_schema)

    @staticmethod
    def deserialize_attendance_time(data: Dict) -> Dict:
        """출퇴근 시간 데이터 역직렬화"""
        return Serializer.deserialize(data, attendance_time_schema)


class IssueSerializer:
    """이슈 관련 직렬화 함수들"""

    @staticmethod
    def serialize_issue(issue) -> Dict:
        """단일 이슈 직렬화"""
        return Serializer.serialize(issue, issue_schema)

    @staticmethod
    def serialize_issues(issues: List) -> List[Dict]:
        """여러 이슈 직렬화"""
        return Serializer.serialize(issues, issues_schema, many=True)

    @staticmethod
    def serialize_issue_comment(comment) -> Dict:
        """단일 이슈 댓글 직렬화"""
        return Serializer.serialize(comment, issue_comment_schema)

    @staticmethod
    def serialize_issue_comments(comments: List) -> List[Dict]:
        """여러 이슈 댓글 직렬화"""
        return Serializer.serialize(comments, issue_comments_schema, many=True)

    @staticmethod
    def deserialize_issue_create(data: Dict) -> Dict:
        """이슈 생성 데이터 역직렬화"""
        return Serializer.deserialize(data, issue_create_schema)

    @staticmethod
    def deserialize_issue_comment_create(data: Dict) -> Dict:
        """이슈 댓글 생성 데이터 역직렬화"""
        return Serializer.deserialize(data, issue_comment_create_schema)

    @staticmethod
    def deserialize_issue_resolve(data: Dict) -> Dict:
        """이슈 해결 데이터 역직렬화"""
        return Serializer.deserialize(data, issue_resolve_schema)


class NoticeSerializer:
    """공지사항 관련 직렬화 함수들"""

    @staticmethod
    def serialize_notice(notice) -> Dict:
        """단일 공지사항 직렬화"""
        return Serializer.serialize(notice, notice_schema)

    @staticmethod
    def serialize_notices(notices: List) -> List[Dict]:
        """여러 공지사항 직렬화"""
        return Serializer.serialize(notices, notices_schema, many=True)

    @staticmethod
    def serialize_notice_read(read) -> Dict:
        """단일 공지사항 읽음 정보 직렬화"""
        return Serializer.serialize(read, notice_read_schema)

    @staticmethod
    def serialize_notice_reads(reads: List) -> List[Dict]:
        """여러 공지사항 읽음 정보 직렬화"""
        return Serializer.serialize(reads, notice_reads_schema, many=True)

    @staticmethod
    def deserialize_notice_create(data: Dict) -> Dict:
        """공지사항 생성 데이터 역직렬화"""
        return Serializer.deserialize(data, notice_create_schema)

    @staticmethod
    def deserialize_notice_update(data: Dict) -> Dict:
        """공지사항 수정 데이터 역직렬화"""
        return Serializer.deserialize(data, notice_update_schema, partial=True)

    @staticmethod
    def deserialize_notice_read_create(data: Dict) -> Dict:
        """공지사항 읽음 처리 데이터 역직렬화"""
        return Serializer.deserialize(data, notice_read_create_schema)

    @staticmethod
    def deserialize_notice_delete(data: Dict) -> Dict:
        """공지사항 삭제 데이터 역직렬화"""
        return Serializer.deserialize(data, notice_delete_schema)


class TaskSerializer:
    """작업 관련 직렬화 함수들"""

    @staticmethod
    def serialize_task_item(task_item) -> Dict:
        """단일 작업 항목 직렬화"""
        return Serializer.serialize(task_item, task_item_schema)

    @staticmethod
    def serialize_task_items(task_items: List) -> List[Dict]:
        """여러 작업 항목 직렬화"""
        return Serializer.serialize(task_items, task_items_schema, many=True)

    @staticmethod
    def serialize_task_checklist(checklist) -> Dict:
        """단일 작업 체크리스트 직렬화"""
        return Serializer.serialize(checklist, task_checklist_schema)

    @staticmethod
    def serialize_task_checklists(checklists: List) -> List[Dict]:
        """여러 작업 체크리스트 직렬화"""
        return Serializer.serialize(checklists, task_checklists_schema, many=True)

    @staticmethod
    def deserialize_task_item_create(data: Dict) -> Dict:
        """작업 항목 생성 데이터 역직렬화"""
        return Serializer.deserialize(data, task_item_create_schema)

    @staticmethod
    def deserialize_task_checklist_create(data: Dict) -> Dict:
        """작업 체크리스트 생성 데이터 역직렬화"""
        return Serializer.deserialize(data, task_checklist_create_schema)

    @staticmethod
    def deserialize_task_update(data: Dict) -> Dict:
        """작업 체크리스트 업데이트 데이터 역직렬화"""
        return Serializer.deserialize(data, task_update_schema)

    @staticmethod
    def deserialize_irregular_task_create(data: Dict) -> Dict:
        """불규칙 업무 생성 데이터 역직렬화"""
        return Serializer.deserialize(data, irregular_task_create_schema)

    @staticmethod
    def save_task_checklist(session, data: Dict):
        """체크리스트 저장/업데이트"""
        from datetime import datetime, timedelta
        from app.models.models import TaskItem, TaskChecklist

        # 데이터 검증
        validated_data = TaskSerializer.deserialize_task_update(data)

        # 현재 날짜 가져오기 (시간 제외)
        current_date = datetime.now().date()

        for update in validated_data["updates"]:
            task_name = update.get("task_name")
            is_checked = update.get("is_checked", False)

            # task_id 찾기
            task = (
                session.query(TaskItem).filter(TaskItem.task_name == task_name).first()
            )
            if not task:
                continue

            # 동일 날짜의 기존 데이터 확인
            existing_record = (
                session.query(TaskChecklist)
                .filter(
                    TaskChecklist.task_id == task.id,
                    TaskChecklist.training_course == validated_data["training_course"],
                    TaskChecklist.checked_date >= current_date,
                    TaskChecklist.checked_date < current_date + timedelta(days=1),
                )
                .first()
            )

            if existing_record:
                # 기존 데이터가 있으면 업데이트
                existing_record.is_checked = is_checked
                existing_record.checked_date = datetime.now()
                existing_record.username = validated_data["username"]
            else:
                # 기존 데이터가 없으면 새로 삽입
                checklist = TaskChecklist(
                    task_id=task.id,
                    training_course=validated_data["training_course"],
                    is_checked=is_checked,
                    username=validated_data["username"],
                )
                session.add(checklist)

    @staticmethod
    def update_task_checklist(session, data: Dict) -> Dict:
        """체크리스트 업데이트 (당일 데이터만)"""
        from datetime import datetime, timedelta
        from app.models.models import TaskItem, TaskChecklist

        # 데이터 검증
        validated_data = TaskSerializer.deserialize_task_update(data)

        # 현재 날짜만 사용 (시간 제외)
        today = datetime.now().date()

        updated_count = 0
        not_found_items = []

        for update in validated_data["updates"]:
            task_name = update.get("task_name")
            is_checked = update.get("is_checked", False)

            # task_id 찾기
            task = (
                session.query(TaskItem).filter(TaskItem.task_name == task_name).first()
            )
            if not task:
                not_found_items.append(task_name)
                continue

            # 당일 날짜의 기존 데이터 확인
            existing_record = (
                session.query(TaskChecklist)
                .filter(
                    TaskChecklist.task_id == task.id,
                    TaskChecklist.training_course == validated_data["training_course"],
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

        return {"updated_count": updated_count, "not_found_items": not_found_items}

    @staticmethod
    def get_tasks(session, task_category: str = None) -> List[Dict]:
        """업무 체크리스트 조회"""
        from app.models.models import TaskItem

        # ORM을 사용하여 업무 조회
        tasks_query = session.query(TaskItem).order_by(TaskItem.id.asc())

        if task_category:
            tasks_query = tasks_query.filter(TaskItem.task_category == task_category)

        tasks = tasks_query.all()

        # Serializer를 사용한 데이터 직렬화
        return TaskSerializer.serialize_task_items(tasks)


class UncheckedSerializer:
    """미해결 항목 관련 직렬화 함수들"""

    @staticmethod
    def serialize_unchecked_description(description) -> Dict:
        """단일 미해결 항목 직렬화"""
        return Serializer.serialize(description, unchecked_description_schema)

    @staticmethod
    def serialize_unchecked_descriptions(descriptions: List) -> List[Dict]:
        """여러 미해결 항목 직렬화"""
        return Serializer.serialize(
            descriptions, unchecked_descriptions_schema, many=True
        )

    @staticmethod
    def serialize_unchecked_comment(comment) -> Dict:
        """단일 미해결 댓글 직렬화"""
        return Serializer.serialize(comment, unchecked_comment_schema)

    @staticmethod
    def serialize_unchecked_comments(comments: List) -> List[Dict]:
        """여러 미해결 댓글 직렬화"""
        return Serializer.serialize(comments, unchecked_comments_schema, many=True)

    @staticmethod
    def deserialize_unchecked_description_create(data: Dict) -> Dict:
        """미해결 항목 생성 데이터 역직렬화"""
        return Serializer.deserialize(data, unchecked_description_create_schema)

    @staticmethod
    def deserialize_unchecked_comment_create(data: Dict) -> Dict:
        """미해결 댓글 생성 데이터 역직렬화"""
        return Serializer.deserialize(data, unchecked_comment_create_schema)

    @staticmethod
    def deserialize_unchecked_resolve(data: Dict) -> Dict:
        """미해결 항목 해결 데이터 역직렬화"""
        return Serializer.deserialize(data, unchecked_resolve_schema)

    @staticmethod
    def get_irregular_tasks(session) -> List[Dict]:
        """비정기 업무 목록 조회"""
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

        return tasks

    @staticmethod
    def create_irregular_task(
        session, task_name: str, training_course: str, is_checked: bool
    ):
        """비정기 업무 생성"""
        from app.models.models import (
            UncheckedDescription,
        )  # Temporarily here, should be refactored to a repository

        irregular_task = UncheckedDescription(
            content=task_name,
            training_course=training_course,
            resolved=is_checked,
        )
        session.add(irregular_task)
        return irregular_task

    @staticmethod
    def save_irregular_tasks(session, data: Dict):
        """비정기 업무 저장"""
        # 데이터 검증
        validated_data = TaskSerializer.deserialize_irregular_task_create(data)

        for update in validated_data["updates"]:
            task_name = update.get("task_name")
            is_checked = update.get("is_checked")

            # Serializer를 사용한 비정기 업무 생성
            UncheckedSerializer.create_irregular_task(
                session, task_name, validated_data["training_course"], is_checked
            )


class TrainingSerializer:
    """교육 관련 직렬화 함수들"""

    @staticmethod
    def serialize_training_info(training_info) -> Dict:
        """단일 교육 정보 직렬화"""
        return Serializer.serialize(training_info, training_info_schema)

    @staticmethod
    def serialize_training_infos(training_infos: List) -> List[Dict]:
        """여러 교육 정보 직렬화"""
        return Serializer.serialize(training_infos, training_infos_schema, many=True)

    @staticmethod
    def deserialize_training_info_create(data: Dict) -> Dict:
        """교육 정보 생성 데이터 역직렬화"""
        return Serializer.deserialize(data, training_info_create_schema)

    @staticmethod
    def deserialize_training_info_update(data: Dict) -> Dict:
        """교육 정보 수정 데이터 역직렬화"""
        return Serializer.deserialize(data, training_info_update_schema, partial=True)


class UserLastCheckSerializer:
    """사용자 마지막 확인 관련 직렬화 함수들"""

    @staticmethod
    def serialize_user_last_check(last_check) -> Dict:
        """단일 사용자 마지막 확인 정보 직렬화"""
        return Serializer.serialize(last_check, user_last_check_schema)

    @staticmethod
    def serialize_user_last_checks(last_checks: List) -> List[Dict]:
        """여러 사용자 마지막 확인 정보 직렬화"""
        return Serializer.serialize(last_checks, user_last_checks_schema, many=True)

    @staticmethod
    def deserialize_user_last_check_update(data: Dict) -> Dict:
        """사용자 마지막 확인 정보 업데이트 데이터 역직렬화"""
        return Serializer.deserialize(data, user_last_check_update_schema, partial=True)


class NotificationSerializer:
    """알림 관련 직렬화 함수들"""

    @staticmethod
    def deserialize_notification_query(data: Dict) -> Dict:
        """알림 조회 데이터 역직렬화"""
        return Serializer.deserialize(data, notification_query_schema)


# ============================================================================
# Flask 응답 헬퍼 함수들
# ============================================================================


def json_response(data: Any, message: str = "성공", status_code: int = 200) -> tuple:
    """
    JSON 응답 생성

    Args:
        data: 응답 데이터
        message: 응답 메시지
        status_code: HTTP 상태 코드

    Returns:
        Flask 응답 튜플
    """
    response = ResponseSerializer.success_response(data=data, message=message)
    return jsonify(response), status_code


def error_json_response(
    error: str, details: Dict = None, status_code: int = 400
) -> tuple:
    """
    에러 JSON 응답 생성

    Args:
        error: 에러 메시지
        details: 상세 에러 정보
        status_code: HTTP 상태 코드

    Returns:
        Flask 응답 튜플
    """
    response = ResponseSerializer.error_response(
        error=error, details=details, status_code=status_code
    )
    return jsonify(response), status_code


def pagination_json_response(
    items: List[Any],
    page: int,
    per_page: int,
    total: int,
    schema: Schema,
    message: str = "성공",
) -> tuple:
    """
    페이지네이션 JSON 응답 생성

    Args:
        items: 아이템 리스트
        page: 현재 페이지
        per_page: 페이지당 아이템 수
        total: 전체 아이템 수
        schema: 직렬화할 스키마
        message: 응답 메시지

    Returns:
        Flask 응답 튜플
    """
    response = ResponseSerializer.pagination_response(
        items=items, page=page, per_page=per_page, total=total, schema=schema
    )
    response["message"] = message
    return jsonify(response), 200


# ============================================================================
# 예외 처리 데코레이터
# ============================================================================


def handle_serialization_errors(func):
    """
    직렬화/역직렬화 에러를 처리하는 데코레이터
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            return error_json_response(
                error="데이터 검증 실패", details=e.messages, status_code=400
            )
        except Exception as e:
            return error_json_response(
                error="서버 내부 오류", details={"detail": str(e)}, status_code=500
            )

    return wrapper
