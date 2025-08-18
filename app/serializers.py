from typing import Any, Dict, List, Optional, Tuple
from marshmallow import ValidationError, Schema
from flask import jsonify
import bcrypt
import re
from datetime import datetime, timedelta

# 모든 스키마 imports
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
    # 추가 검증용 스키마
    task_update_schema,
    irregular_task_create_schema,
    unchecked_resolve_schema,
    notice_read_create_schema,
    notice_delete_schema,
    issue_resolve_schema,
    notification_query_schema,
    # 응답 스키마
    response_schema,
    error_schema,
    pagination_schema,
)

# 모든 모델 imports
from app.models.models import (
    User,
    Attendance,
    Issue,
    IssueComment,
    Notice,
    NoticeRead,
    TaskItem,
    TaskChecklist,
    UncheckedDescription,
    UncheckedComment,
    TrainingInfo,
    UserLastCheck,
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
        """비밀번호가 이미 해시되었는지 확인"""
        return password.startswith("$2b$")

    @staticmethod
    def login(session, data: Dict) -> Dict:
        """로그인 처리"""
        # 데이터 검증
        validated_data = UserSerializer.deserialize_user_login(data)

        # 사용자 조회
        user = (
            session.query(User)
            .filter(User.username == validated_data["username"])
            .first()
        )

        if not user:
            raise ValueError("잘못된 ID 또는 비밀번호입니다.")

        # 비밀번호 검증 (bcrypt 사용)
        if not UserSerializer.verify_password(
            validated_data["password"], user.password
        ):
            raise ValueError("잘못된 ID 또는 비밀번호입니다.")

        return {"user_id": user.id, "username": user.username, "role": user.role}

    @staticmethod
    def change_password(session, data: Dict):
        """비밀번호 변경"""
        # 데이터 검증
        validated_data = UserSerializer.deserialize_password_change(data)

        # 현재 비밀번호 확인
        user = (
            session.query(User)
            .filter(User.username == validated_data["username"])
            .first()
        )

        if not user:
            raise ValueError("사용자명 또는 현재 비밀번호가 일치하지 않습니다.")

        # 현재 비밀번호 검증 (bcrypt 사용)
        if not UserSerializer.verify_password(
            validated_data["current_password"], user.password
        ):
            raise ValueError("사용자명 또는 현재 비밀번호가 일치하지 않습니다.")

        # 새 비밀번호 해싱
        hashed_new_password = UserSerializer.hash_password(
            validated_data["new_password"]
        )

        user.password = hashed_new_password
        return user


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
    def save_attendance(session, data: Dict):
        """출퇴근 기록 저장"""
        # 데이터 검증
        validated_data = AttendanceSerializer.deserialize_attendance_create(data)

        # 시간 문자열을 Time 객체로 변환
        check_in_time = (
            datetime.strptime(validated_data.get("check_in_time", ""), "%H:%M").time()
            if validated_data.get("check_in_time")
            else None
        )
        check_out_time = (
            datetime.strptime(validated_data.get("check_out_time", ""), "%H:%M").time()
            if validated_data.get("check_out_time")
            else None
        )

        attendance = Attendance(
            date=validated_data["date"],
            instructor=validated_data.get("instructor"),
            instructor_name=validated_data.get("instructor_name"),
            training_course=validated_data.get("training_course"),
            check_in_time=check_in_time,
            check_out_time=check_out_time,
            daily_log=validated_data.get("daily_log", False),
        )

        session.add(attendance)
        session.flush()  # ID를 얻기 위해 flush

        # 저장된 데이터 직렬화
        return AttendanceSerializer.serialize_attendance(attendance)

    @staticmethod
    def get_attendance(session) -> List[Dict]:
        """출퇴근 기록 조회"""
        attendance_query = session.query(Attendance).order_by(Attendance.date.desc())
        attendance_records = attendance_query.all()

        # Serializer를 사용한 데이터 직렬화
        return AttendanceSerializer.serialize_attendances(attendance_records)


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

    @staticmethod
    def create_issue(session, data: Dict) -> Dict:
        """이슈 생성"""
        # 데이터 검증
        validated_data = IssueSerializer.deserialize_issue_create(data)

        # 이슈 생성
        issue = Issue(
            content=validated_data["content"],
            training_course=validated_data.get("training_course"),
            username=validated_data.get("username"),
            created_by=validated_data.get("created_by", validated_data.get("username")),
            date=validated_data.get("date"),
            resolved=False,
        )

        session.add(issue)
        session.flush()  # ID를 얻기 위해 flush

        return {"id": issue.id, **validated_data}

    @staticmethod
    def get_issues(session) -> List[Dict]:
        """해결되지 않은 이슈 목록 조회"""
        # ORM을 사용하여 해결되지 않은 이슈 조회
        issues_query = (
            session.query(Issue)
            .filter(Issue.resolved == False)
            .order_by(Issue.created_at.desc())
        )
        issues = issues_query.all()

        # Serializer를 사용한 데이터 직렬화
        serialized_issues = IssueSerializer.serialize_issues(issues)

        # 교육과정별로 그룹화
        issues_grouped = {}
        for issue, serialized_issue in zip(issues, serialized_issues):
            course = issue.training_course
            if course not in issues_grouped:
                issues_grouped[course] = []

            # 댓글 조회 및 직렬화
            comments = (
                session.query(IssueComment)
                .filter(IssueComment.issue_id == issue.id)
                .all()
            )
            serialized_comments = IssueSerializer.serialize_issue_comments(comments)

            # 댓글 정보를 이슈에 추가
            serialized_issue["comments"] = serialized_comments
            issues_grouped[course].append(serialized_issue)

        # 응답 형식 변환
        response_data = [
            {"training_course": course, "issues": issues_list}
            for course, issues_list in issues_grouped.items()
        ]

        return response_data

    @staticmethod
    def add_comment(session, data: Dict):
        """이슈 댓글 추가"""
        # 데이터 검증
        validated_data = IssueSerializer.deserialize_issue_comment_create(data)

        # 댓글 생성
        comment = IssueComment(
            issue_id=validated_data["issue_id"],
            comment=validated_data["comment"],
            created_by=validated_data["created_by"],
        )

        session.add(comment)
        session.flush()  # ID를 얻기 위해 flush

        return {"id": comment.id, **validated_data}

    @staticmethod
    def resolve_issue(session, data: Dict):
        """이슈 해결"""
        # 데이터 검증
        validated_data = IssueSerializer.deserialize_issue_resolve(data)

        issue = (
            session.query(Issue).filter(Issue.id == validated_data["issue_id"]).first()
        )
        if not issue:
            raise ValueError("이슈를 찾을 수 없습니다.")

        issue.resolved = True

        # 업데이트된 이슈 직렬화
        return IssueSerializer.serialize_issue(issue)

    @staticmethod
    def get_issue_comments(session, issue_id: str) -> List[Dict]:
        """특정 이슈에 대한 댓글 목록 조회"""
        if not issue_id:
            raise ValueError("이슈 ID를 입력하세요.")

        comments_query = (
            session.query(IssueComment)
            .filter(IssueComment.issue_id == issue_id)
            .order_by(IssueComment.created_at.asc())
        )

        comments = comments_query.all()

        # Serializer를 사용한 데이터 직렬화
        return IssueSerializer.serialize_issue_comments(comments)

    @staticmethod
    def get_all_issues(session) -> List[Dict]:
        """모든 이슈 목록 조회 (다운로드용)"""
        issues_query = session.query(Issue).all()

        # Serializer를 사용한 데이터 직렬화
        return IssueSerializer.serialize_issues(issues_query)


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

    @staticmethod
    def add_notice(session, data: Dict) -> Dict:
        """공지사항 추가"""
        # 데이터 검증
        validated_data = NoticeSerializer.deserialize_notice_create(data)

        # 허용된 사용자 확인
        allowed_users = ["김은지", "장지연", "김슬기"]
        if validated_data.get("created_by") not in allowed_users:
            raise ValueError("공지사항 작성 권한이 없습니다.")

        # 공지사항 생성
        notice = Notice(
            title=validated_data["title"],
            content=validated_data["content"],
            type=validated_data.get("type", "공지사항"),
            created_by=validated_data.get("created_by"),
        )

        session.add(notice)
        session.flush()  # ID를 얻기 위해 flush

        # 저장된 공지사항 직렬화
        serialized_notice = NoticeSerializer.serialize_notice(notice)

        return {"id": notice.id, **serialized_notice}

    @staticmethod
    def get_notices(session) -> List[Dict]:
        """공지사항 조회"""
        # ORM을 사용하여 공지사항 조회
        notices_query = (
            session.query(Notice)
            .filter(Notice.is_deleted == False)
            .order_by(Notice.date.desc())
        )
        notices = []

        for notice in notices_query.all():
            notice_dict = {
                "id": notice.id,
                "type": notice.type or "공지사항",
                "title": notice.title,
                "content": notice.content,
                "date": notice.date.strftime("%Y-%m-%d %H:%M:%S"),
                "created_by": notice.created_by,
            }
            notices.append(notice_dict)

        return notices

    @staticmethod
    def update_notice(session, notice_id: int, data: Dict):
        """공지사항 수정"""
        # 데이터 검증
        validated_data = NoticeSerializer.deserialize_notice_update(data)

        # 수정자 정보 추출
        username = validated_data.get("username")

        if not username:
            raise ValueError("수정자 정보가 누락되었습니다.")

        # 공지사항 존재 확인
        notice = session.query(Notice).filter(Notice.id == notice_id).first()

        if not notice:
            raise ValueError("해당 공지사항을 찾을 수 없습니다.")

        # 공지사항 업데이트
        notice.title = validated_data.get("title")
        notice.content = validated_data.get("content")
        notice.type = validated_data.get("type")
        notice.modified_by = username

        # 수정된 공지사항 직렬화
        return NoticeSerializer.serialize_notice(notice)

    @staticmethod
    def delete_notice(session, notice_id: int):
        """공지사항 삭제 (soft delete)"""
        # 공지사항 존재 확인
        notice = session.query(Notice).filter(Notice.id == notice_id).first()

        if not notice:
            raise ValueError("해당 공지사항을 찾을 수 없습니다.")

        # 공지사항 삭제 (soft delete)
        notice.is_deleted = True

        # 삭제된 공지사항 직렬화
        return NoticeSerializer.serialize_notice(notice)

    @staticmethod
    def mark_notice_read(session, data: Dict):
        """공지사항 읽음 표시"""
        # 데이터 검증
        validated_data = NoticeSerializer.deserialize_notice_read_create(data)

        # 공지사항 존재 확인
        notice = (
            session.query(Notice)
            .filter(Notice.id == validated_data["notice_id"])
            .first()
        )
        if not notice:
            raise ValueError("공지사항을 찾을 수 없습니다.")

        # 이미 읽었는지 확인
        existing_read = (
            session.query(NoticeRead)
            .filter(
                NoticeRead.notice_id == validated_data["notice_id"],
                NoticeRead.username == validated_data["username"],
            )
            .first()
        )

        if not existing_read:
            # 읽음 표시 추가
            notice_read = NoticeRead(
                notice_id=validated_data["notice_id"],
                username=validated_data["username"],
            )
            session.add(notice_read)
            session.flush()  # ID를 얻기 위해 flush
        else:
            notice_read = existing_read

        # 읽음 표시 직렬화
        return NoticeSerializer.serialize_notice_read(notice_read)

    @staticmethod
    def get_notice_reads(session, notice_id: str) -> List[Dict]:
        """공지사항별 읽은 사용자 목록 조회"""
        if not notice_id:
            raise ValueError("공지사항 ID가 필요합니다.")

        # 공지사항 읽음 기록 조회
        reads_query = (
            session.query(NoticeRead)
            .filter(NoticeRead.notice_id == notice_id)
            .order_by(NoticeRead.read_at.desc())
        )

        reads_data = []
        for notice_read in reads_query.all():
            reads_data.append(
                {
                    "username": notice_read.username,
                    "read_at": notice_read.read_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

        return reads_data


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

    @staticmethod
    def get_unchecked_descriptions(session) -> List[Dict]:
        """미체크 항목 설명 및 액션 플랜 조회 (부서명 포함)"""
        unchecked_items = []
        items = (
            session.query(UncheckedDescription)
            .filter(UncheckedDescription.resolved == False)
            .order_by(UncheckedDescription.created_at.desc())
            .all()
        )

        for item in items:
            # 부서명 조회
            dept = None
            if item.training_course:
                training_info = (
                    session.query(TrainingInfo)
                    .filter(TrainingInfo.training_course == item.training_course)
                    .first()
                )
                if training_info:
                    dept = training_info.dept

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

        return unchecked_items

    @staticmethod
    def save_unchecked_description(session, data: Dict):
        """미체크 항목 설명과 액션 플랜 저장"""
        # 데이터 검증
        validated_data = UncheckedSerializer.deserialize_unchecked_description_create(
            data
        )

        unchecked_description = UncheckedDescription(
            content=validated_data["content"],
            action_plan=validated_data.get("action_plan"),
            training_course=validated_data.get("training_course"),
            resolved=False,
        )

        session.add(unchecked_description)
        return unchecked_description

    @staticmethod
    def resolve_unchecked_description(session, data: Dict):
        """미체크 항목 해결"""
        # 데이터 검증
        validated_data = UncheckedSerializer.deserialize_unchecked_resolve(data)

        unchecked_item = (
            session.query(UncheckedDescription)
            .filter(UncheckedDescription.id == validated_data["unchecked_id"])
            .first()
        )

        if not unchecked_item:
            raise ValueError("미체크 항목을 찾을 수 없습니다.")

        unchecked_item.resolved = True
        return unchecked_item

    @staticmethod
    def add_unchecked_comment(session, data: Dict):
        """미체크 항목에 댓글 추가"""
        # 데이터 검증
        validated_data = UncheckedSerializer.deserialize_unchecked_comment_create(data)

        unchecked_comment = UncheckedComment(
            unchecked_id=validated_data["unchecked_id"],
            comment=validated_data["comment"],
        )

        session.add(unchecked_comment)
        return unchecked_comment

    @staticmethod
    def get_unchecked_comments(session, unchecked_id: int) -> List[Dict]:
        """미체크 항목의 댓글 조회"""
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

        return comments


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

    @staticmethod
    def get_training_courses(session) -> List[str]:
        """훈련 과정 목록 조회 (현재 진행 중이거나 종료된 지 1주일 이내의 과정만)"""
        # 현재 날짜 기준으로 종료된 지 1주일 이내이거나 아직 진행 중인 과정만 조회
        one_week_ago = datetime.now().date() - timedelta(days=7)
        courses_query = (
            session.query(TrainingInfo)
            .filter(TrainingInfo.end_date >= one_week_ago)
            .order_by(TrainingInfo.start_date.desc())
        )

        courses = courses_query.all()

        # Serializer를 사용한 데이터 직렬화
        serialized_courses = TrainingSerializer.serialize_training_infos(courses)
        course_names = [course["training_course"] for course in serialized_courses]

        return course_names

    @staticmethod
    def save_training_info(session, data: Dict):
        """훈련 과정 정보 저장"""
        # 데이터 검증
        validated_data = TrainingSerializer.deserialize_training_info_create(data)

        # 날짜 문자열을 Date 객체로 변환
        start_date_obj = datetime.strptime(
            validated_data["start_date"], "%Y-%m-%d"
        ).date()
        end_date_obj = datetime.strptime(validated_data["end_date"], "%Y-%m-%d").date()

        training_info = TrainingInfo(
            training_course=validated_data["training_course"],
            start_date=start_date_obj,
            end_date=end_date_obj,
            dept=validated_data["dept"],
            manager_name=validated_data["manager_name"],
        )

        session.add(training_info)
        return training_info

    @staticmethod
    def get_training_info(session) -> List[Dict]:
        """훈련 과정 목록 조회"""
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

        return courses_data


class NotificationSerializer:
    """알림 관련 직렬화 함수들"""

    @staticmethod
    def deserialize_notification_query(data: Dict) -> Dict:
        """알림 조회 데이터 역직렬화"""
        return Serializer.deserialize(data, notification_query_schema)

    @staticmethod
    def get_unread_count(session, data: Dict) -> Dict:
        """사용자별 미확인 알림 개수 조회"""
        # 데이터 검증
        validated_data = NotificationSerializer.deserialize_notification_query(data)

        # 사용자의 마지막 확인 시간 조회
        last_check = (
            session.query(UserLastCheck)
            .filter(UserLastCheck.username == validated_data["username"])
            .first()
        )

        if not last_check:
            # 첫 로그인인 경우 현재 시간으로 초기화
            last_check = UserLastCheck(
                username=validated_data["username"],
                last_notice_check=datetime.now(),
                last_issue_check=datetime.now(),
                last_comment_check=datetime.now(),
            )
            session.add(last_check)
            session.flush()  # 커밋하지 않고 flush만 실행
            return {
                "new_notices": 0,
                "new_issues": 0,
                "new_comments": 0,
            }

        # 새로운 항목 개수 조회
        new_notices = (
            session.query(Notice)
            .filter(
                Notice.date > last_check.last_notice_check,
                Notice.is_deleted == False,
            )
            .count()
        )

        new_issues = (
            session.query(Issue)
            .filter(Issue.created_at > last_check.last_issue_check)
            .count()
        )

        new_comments = (
            session.query(IssueComment)
            .filter(IssueComment.created_at > last_check.last_comment_check)
            .count()
        )

        # 현재 시간으로 마지막 확인 시간 업데이트
        last_check.last_notice_check = datetime.now()
        last_check.last_issue_check = datetime.now()
        last_check.last_comment_check = datetime.now()

        return {
            "new_notices": new_notices,
            "new_issues": new_issues,
            "new_comments": new_comments,
        }


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
