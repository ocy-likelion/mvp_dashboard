"""
Training service for training-related business logic
"""

from typing import Dict, List
from datetime import datetime, timedelta

from app.utils.database import db_session, db_session_read_only
from .base_service import BaseService
from app.models.models import TrainingInfo


class TrainingService(BaseService):
    """교육 관련 비즈니스 로직 처리"""

    @staticmethod
    def get_active_training_courses() -> List[str]:
        """현재 진행 중이거나 종료된 지 1주일 이내의 훈련 과정 목록 조회"""
        with db_session_read_only() as session:
            # 현재 날짜 기준으로 종료된 지 1주일 이내이거나 아직 진행 중인 과정만 조회
            one_week_ago = datetime.now().date() - timedelta(days=7)
            courses_query = (
                session.query(TrainingInfo)
                .filter(TrainingInfo.end_date >= one_week_ago)
                .order_by(TrainingInfo.start_date.desc())
            )

            courses = courses_query.all()
            course_names = [course.training_course for course in courses]

            return course_names

    @staticmethod
    def create_training_info(training_data: Dict) -> TrainingInfo:
        """훈련 과정 정보 저장"""
        with db_session() as session:
            # 중복 과정명 확인
            existing_course = (
                session.query(TrainingInfo)
                .filter(TrainingInfo.training_course == training_data["training_course"])
                .first()
            )
            if existing_course:
                raise ValueError("이미 존재하는 훈련 과정명입니다.")

            # 날짜 문자열을 Date 객체로 변환
            start_date_obj = None
            end_date_obj = None

            if training_data.get("start_date"):
                try:
                    start_date_obj = datetime.strptime(
                        training_data["start_date"], "%Y-%m-%d"
                    ).date()
                except ValueError:
                    raise ValueError(
                        "시작 날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식을 사용해주세요."
                    )

            if training_data.get("end_date"):
                try:
                    end_date_obj = datetime.strptime(
                        training_data["end_date"], "%Y-%m-%d"
                    ).date()
                except ValueError:
                    raise ValueError(
                        "종료 날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식을 사용해주세요."
                    )

            # 날짜 유효성 검증
            if start_date_obj and end_date_obj and start_date_obj > end_date_obj:
                raise ValueError("시작 날짜는 종료 날짜보다 이전이어야 합니다.")

            training_info = TrainingInfo(
                training_course=training_data["training_course"],
                start_date=start_date_obj,
                end_date=end_date_obj,
                dept=training_data.get("dept"),
                manager_name=training_data.get("manager_name"),
            )

            TrainingService.flush_and_get_id(session, training_info)
            return training_info

    @staticmethod
    def get_all_training_info() -> List[Dict]:
        """모든 훈련 과정 목록 조회"""
        with db_session_read_only() as session:
            courses_query = session.query(TrainingInfo).order_by(
                TrainingInfo.start_date.desc()
            )
            courses = courses_query.all()

            courses_data = []
            for course in courses:
                courses_data.append(
                    {
                        "id": course.id,
                        "training_course": course.training_course,
                        "start_date": (
                            course.start_date.strftime("%Y-%m-%d")
                            if course.start_date
                            else None
                        ),
                        "end_date": (
                            course.end_date.strftime("%Y-%m-%d")
                            if course.end_date
                            else None
                        ),
                        "dept": course.dept,
                        "manager_name": course.manager_name,
                    }
                )

            return courses_data

    @staticmethod
    def get_training_by_course_name(course_name: str) -> TrainingInfo:
        """과정명으로 훈련 정보 조회"""
        with db_session_read_only() as session:
            training = (
                session.query(TrainingInfo)
                .filter(TrainingInfo.training_course == course_name)
                .first()
            )
            if not training:
                raise ValueError(f"훈련 과정을 찾을 수 없습니다: {course_name}")

            return training

    @staticmethod
    def update_training_info(training_id: int, update_data: Dict) -> TrainingInfo:
        """훈련 과정 정보 수정"""
        with db_session() as session:
            training = TrainingService.safe_get_by_id(
                session, TrainingInfo, training_id, "훈련 과정을 찾을 수 없습니다."
            )

            # 과정명 중복 확인 (다른 과정과의 중복)
            if "training_course" in update_data:
                existing_course = (
                    session.query(TrainingInfo)
                    .filter(
                        TrainingInfo.training_course == update_data["training_course"],
                        TrainingInfo.id != training_id,
                    )
                    .first()
                )
                if existing_course:
                    raise ValueError("이미 존재하는 훈련 과정명입니다.")

            # 날짜 필드 업데이트
            if "start_date" in update_data and update_data["start_date"]:
                try:
                    training.start_date = datetime.strptime(
                        update_data["start_date"], "%Y-%m-%d"
                    ).date()
                except ValueError:
                    raise ValueError(
                        "시작 날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식을 사용해주세요."
                    )

            if "end_date" in update_data and update_data["end_date"]:
                try:
                    training.end_date = datetime.strptime(
                        update_data["end_date"], "%Y-%m-%d"
                    ).date()
                except ValueError:
                    raise ValueError(
                        "종료 날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식을 사용해주세요."
                    )

            # 날짜 유효성 검증
            if (
                training.start_date
                and training.end_date
                and training.start_date > training.end_date
            ):
                raise ValueError("시작 날짜는 종료 날짜보다 이전이어야 합니다.")

            # 기타 필드 업데이트
            allowed_fields = ["training_course", "dept", "manager_name"]
            for field, value in update_data.items():
                if field in allowed_fields and hasattr(training, field):
                    setattr(training, field, value)

            return training

    @staticmethod
    def delete_training_info(training_id: int) -> None:
        """훈련 과정 정보 삭제"""
        with db_session() as session:
            training = TrainingService.safe_get_by_id(
                session, TrainingInfo, training_id, "훈련 과정을 찾을 수 없습니다."
            )
            session.delete(training)

    @staticmethod
    def get_training_by_dept(dept: str) -> List[TrainingInfo]:
        """부서별 훈련 과정 조회"""
        with db_session_read_only() as session:
            return (
                session.query(TrainingInfo)
                .filter(TrainingInfo.dept == dept)
                .order_by(TrainingInfo.start_date.desc())
                .all()
            )

    @staticmethod
    def get_training_by_manager(manager_name: str) -> List[TrainingInfo]:
        """담당자별 훈련 과정 조회"""
        with db_session_read_only() as session:
            return (
                session.query(TrainingInfo)
                .filter(TrainingInfo.manager_name == manager_name)
                .order_by(TrainingInfo.start_date.desc())
                .all()
            )

    @staticmethod
    def get_current_training_courses() -> List[TrainingInfo]:
        """현재 진행 중인 훈련 과정 조회"""
        with db_session_read_only() as session:
            today = datetime.now().date()
            return (
                session.query(TrainingInfo)
                .filter(TrainingInfo.start_date <= today, TrainingInfo.end_date >= today)
                .order_by(TrainingInfo.start_date.desc())
                .all()
            )

    @staticmethod
    def get_upcoming_training_courses(days_ahead: int = 30) -> List[TrainingInfo]:
        """앞으로 시작될 훈련 과정 조회"""
        with db_session_read_only() as session:
            today = datetime.now().date()
            future_date = today + timedelta(days=days_ahead)

            return (
                session.query(TrainingInfo)
                .filter(
                    TrainingInfo.start_date > today, TrainingInfo.start_date <= future_date
                )
                .order_by(TrainingInfo.start_date.asc())
                .all()
            )

    @staticmethod
    def get_completed_training_courses(days_back: int = 30) -> List[TrainingInfo]:
        """최근 완료된 훈련 과정 조회"""
        with db_session_read_only() as session:
            today = datetime.now().date()
            past_date = today - timedelta(days=days_back)

            return (
                session.query(TrainingInfo)
                .filter(TrainingInfo.end_date < today, TrainingInfo.end_date >= past_date)
                .order_by(TrainingInfo.end_date.desc())
                .all()
            )

    @staticmethod
    def calculate_training_duration(training: TrainingInfo) -> int:
        """훈련 과정 기간 계산 (일 단위)"""
        if not training.start_date or not training.end_date:
            return 0

        duration = training.end_date - training.start_date
        return duration.days + 1  # 시작일과 종료일 포함

    @staticmethod
    def get_training_summary() -> Dict:
        """훈련 과정 요약 정보"""
        with db_session_read_only() as session:
            today = datetime.now().date()

            # 전체 과정 수
            total_courses = session.query(TrainingInfo).count()

            # 현재 진행 중인 과정 수
            current_courses = (
                session.query(TrainingInfo)
                .filter(TrainingInfo.start_date <= today, TrainingInfo.end_date >= today)
                .count()
            )

            # 완료된 과정 수
            completed_courses = (
                session.query(TrainingInfo).filter(TrainingInfo.end_date < today).count()
            )

            # 예정된 과정 수
            upcoming_courses = (
                session.query(TrainingInfo).filter(TrainingInfo.start_date > today).count()
            )

            return {
                "total_courses": total_courses,
                "current_courses": current_courses,
                "completed_courses": completed_courses,
                "upcoming_courses": upcoming_courses,
            }
