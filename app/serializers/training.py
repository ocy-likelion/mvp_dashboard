from typing import Dict, List
from datetime import datetime, timedelta

from .base import Serializer
from app.schemas import (
    training_info_schema,
    training_infos_schema,
    training_info_create_schema,
    training_info_update_schema,
)
from app.models.models import TrainingInfo


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
