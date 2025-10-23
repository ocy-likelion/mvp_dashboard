"""
Attendance service for attendance-related business logic
"""

from typing import Dict, List
from datetime import datetime, time

import io
import pandas as pd
from .base_service import BaseService
from app.models.models import Attendance
from app.utils.database import db_session, db_session_read_only


class AttendanceService(BaseService):
    """출석 관련 비즈니스 로직 처리"""

    @staticmethod
    def create_attendance(attendance_data: Dict) -> Dict:
        """출퇴근 기록 저장"""
        # 시간 문자열을 Time 객체로 변환
        check_in = None
        check_out = None

        if attendance_data.get("check_in"):
            try:
                check_in = datetime.strptime(
                    attendance_data["check_in"], "%H:%M"
                ).time()
            except ValueError:
                raise ValueError(
                    "출근 시간 형식이 올바르지 않습니다. HH:MM 형식을 사용해주세요."
                )

        if attendance_data.get("check_out"):
            try:
                check_out = datetime.strptime(
                    attendance_data["check_out"], "%H:%M"
                ).time()
            except ValueError:
                raise ValueError(
                    "퇴근 시간 형식이 올바르지 않습니다. HH:MM 형식을 사용해주세요."
                )

        # 날짜 유효성 검증
        attendance_date = attendance_data["date"]
        if isinstance(attendance_date, str):
            try:
                attendance_date = datetime.strptime(attendance_date, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(
                    "날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식을 사용해주세요."
                )

        with db_session() as session:
            # 중복 출석 기록 확인
            # existing_attendance = (
            #     session.query(Attendance)
            #     .filter(
            #         Attendance.date == attendance_date,
            #         # Attendance.instructor == attendance_data.get("instructor"),
            #         # 보조 강사가 여러 명으로 추가되는 경우에, instructor 가 2로 고정되어 추가 요청이 발생하는 문제
            #         # 프론트엔드에서 보조 강사 추가 시 instructor 코드를 증가 시키도록 수정한 뒤 이 코드 주석 해제
            #         Attendance.training_course
            #         == attendance_data.get("training_course"),
            #     )
            #     .first()
            # )

            # if existing_attendance:
            #     raise ValueError("해당 날짜에 이미 출석 기록이 존재합니다.")

            attendance = Attendance(
                date=attendance_date,
                instructor=attendance_data.get("instructor"),
                instructor_name=attendance_data.get("instructor_name"),
                training_course=attendance_data.get("training_course"),
                check_in=check_in,
                check_out=check_out,
                daily_log=attendance_data.get("daily_log", False),
            )

            AttendanceService.flush_and_get_id(session, attendance)
            
            # 딕셔너리 형태로 반환
            return {
                "id": attendance.id,
                "date": attendance.date.strftime("%Y-%m-%d"),
                "instructor": attendance.instructor,
                "instructor_name": attendance.instructor_name,
                "training_course": attendance.training_course,
                "check_in": attendance.check_in.strftime("%H:%M") if attendance.check_in else None,
                "check_out": attendance.check_out.strftime("%H:%M") if attendance.check_out else None,
                "daily_log": attendance.daily_log,
            }

    @staticmethod
    def generate_excel_file(serialized_records: List[Dict]) -> io.BytesIO:
        """출퇴근 기록 Excel 파일 생성"""
        if not serialized_records:
            raise ValueError("Excel 생성을 위한 데이터가 없습니다.")

        # Excel 생성을 위한 데이터 변환
        records_data = [
            (
                record["id"],
                record["date"],
                record["instructor"],
                record["training_course"],
                record["check_in"],
                record["check_out"],
                record["daily_log"],
            )
            for record in serialized_records
        ]

        columns = [
            "ID",
            "날짜",
            "강사",
            "훈련과정",
            "출근 시간",
            "퇴근 시간",
            "일지 작성 완료",
        ]

        df = pd.DataFrame(records_data, columns=columns)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="출퇴근 기록")
        output.seek(0)

        return output

    @staticmethod
    def get_attendance_records(limit: int = None) -> List[Attendance]:
        """출퇴근 기록 조회 (기존 메서드 - 하위 호환성 유지)"""
        return AttendanceService.get_attendance_records_paginated({}, limit)["items"]

    @staticmethod
    def get_attendance_records_paginated(filters: Dict, limit: int = None) -> Dict:
        """페이지네이션을 포함한 출퇴근 기록 조회"""
        import logging
        from datetime import datetime
        logger = logging.getLogger(__name__)
        
        try:
            with db_session_read_only() as session:
                query = session.query(Attendance)

                # 월별 필터 적용
                if filters.get("year") and filters.get("month"):
                    year = filters["year"]
                    month = filters["month"]
                    # 해당 월의 시작일과 종료일 계산
                    start_date = datetime(year, month, 1).date()
                    if month == 12:
                        end_date = datetime(year + 1, 1, 1).date()
                    else:
                        end_date = datetime(year, month + 1, 1).date()
                    
                    query = query.filter(
                        Attendance.date >= start_date,
                        Attendance.date < end_date
                    )
                elif filters.get("year"):
                    # 년도만 지정된 경우
                    year = filters["year"]
                    start_date = datetime(year, 1, 1).date()
                    end_date = datetime(year + 1, 1, 1).date()
                    query = query.filter(
                        Attendance.date >= start_date,
                        Attendance.date < end_date
                    )

                # 강사 필터
                if filters.get("instructor"):
                    query = query.filter(Attendance.instructor == filters["instructor"])

                # 훈련 과정 필터
                if filters.get("training_course"):
                    query = query.filter(Attendance.training_course == filters["training_course"])

                # 검색 필터
                if filters.get("search"):
                    search_term = f"%{filters['search']}%"
                    query = query.filter(
                        (Attendance.instructor_name.contains(search_term)) |
                        (Attendance.training_course.contains(search_term))
                    )

                # 전체 개수 조회
                total_count = query.count()
                
                # 정렬 (최신 날짜순)
                query = query.order_by(Attendance.date.desc())
                
                # limit 파라미터가 있으면 페이지네이션 대신 limit 적용
                if limit:
                    records = query.limit(limit).all()
                    return {
                        "items": records,
                        "pagination": {
                            "page": 1,
                            "per_page": limit,
                            "total_count": total_count,
                            "total_pages": 1,
                            "has_next": False,
                            "has_prev": False
                        }
                    }
                
                # 페이지네이션 적용
                page = filters.get("page", 1)
                per_page = filters.get("per_page", 10)
                offset = (page - 1) * per_page
                
                records = query.offset(offset).limit(per_page).all()

                # 페이지네이션 정보 계산
                total_pages = (total_count + per_page - 1) // per_page
                has_next = page < total_pages
                has_prev = page > 1

                return {
                    "items": records,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total_count": total_count,
                        "total_pages": total_pages,
                        "has_next": has_next,
                        "has_prev": has_prev
                    }
                }
        except Exception as e:
            logger.error(f"Error in get_attendance_records_paginated: {str(e)}", exc_info=True)
            # 오류 발생 시 빈 결과 반환
            return {
                "items": [],
                "pagination": {
                    "page": filters.get("page", 1),
                    "per_page": filters.get("per_page", 10),
                    "total_count": 0,
                    "total_pages": 0,
                    "has_next": False,
                    "has_prev": False
                }
            }
