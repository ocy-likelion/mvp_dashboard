"""
Issue service for issue-related business logic
"""

from typing import Dict, List

from app.utils.database import db_session, db_session_read_only
from .base_service import BaseService
from app.models.models import Issue, IssueComment


class IssueService(BaseService):
    """이슈 관련 비즈니스 로직 처리"""

    @staticmethod
    def create_issue(issue_data: Dict) -> Dict:
        """이슈 생성"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            with db_session() as session:
                # 이슈 생성
                issue = Issue(
                    content=issue_data["issue"],  # content → issue로 변경
                    training_course=issue_data.get("training_course"),
                    username=issue_data.get("username"),
                    created_by=issue_data.get("created_by", issue_data.get("username")),
                    date=issue_data.get("date"),
                    resolved=False,
                )

                IssueService.flush_and_get_id(session, issue)
                
                # 딕셔너리 형태로 반환
                return {
                    "id": issue.id,
                    "content": issue.content,
                    "training_course": issue.training_course,
                    "username": issue.username,
                    "created_by": issue.created_by,
                    "date": issue.date.strftime("%Y-%m-%d") if issue.date else None,
                    "created_at": issue.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "resolved": issue.resolved,
                }
        except Exception as e:
            logger.error(f"Error in create_issue: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def get_unresolved_issues() -> List[Dict]:
        """해결되지 않은 이슈 목록 조회 (교육과정별 그룹화)"""
        with db_session_read_only() as session:
            # 해결되지 않은 이슈 조회
            issues = (
                session.query(Issue)
                .filter(Issue.resolved == False)
                .order_by(Issue.created_at.desc())
                .all()
            )

            # 교육과정별로 그룹화
            issues_grouped = {}
            for issue in issues:
                course = issue.training_course
                if course not in issues_grouped:
                    issues_grouped[course] = []

                # 댓글 조회
                comments = (
                    session.query(IssueComment)
                    .filter(IssueComment.issue_id == issue.id)
                    .order_by(IssueComment.created_at.asc())
                    .all()
                )

                issue_data = {
                    "id": issue.id,
                    "content": issue.content,
                    "date": issue.date,  # 기존 함수와 동일하게 날짜 형식 그대로 유지
                    "created_at": issue.created_at,  # 기존 함수와 동일하게 생성일 형식 그대로 유지
                    "created_by": issue.created_by or "작성자 없음",  # 기존 함수와 동일하게 COALESCE 처리
                    "resolved": issue.resolved,
                    "comments": [
                        {
                            "id": comment.id,
                            "comment": comment.comment,
                            "created_at": comment.created_at,
                            "created_by": comment.created_by,
                        }
                        for comment in comments
                    ],
                }
                issues_grouped[course].append(issue_data)

            # 응답 형식 변환
            response_data = [
                {"training_course": course, "issues": issues_list}
                for course, issues_list in issues_grouped.items()
            ]

            return response_data

    @staticmethod
    def get_all_issues() -> List[Issue]:
        """모든 이슈 목록 조회 (다운로드용)"""
        with db_session_read_only() as session:
            return session.query(Issue).order_by(Issue.created_at.desc()).all()

    @staticmethod
    def add_comment(comment_data: Dict) -> IssueComment:
        """이슈 댓글 추가"""
        with db_session() as session:
            # 이슈 존재 확인
            issue = IssueService.safe_get_by_id(
                session, Issue, comment_data["issue_id"], "이슈를 찾을 수 없습니다."
            )

            # 댓글 생성
            comment = IssueComment(
                issue_id=comment_data["issue_id"],
                comment=comment_data["comment"],
                created_by=comment_data["created_by"],
            )

            IssueService.flush_and_get_id(session, comment)
            return comment

    @staticmethod
    def resolve_issue(validated_data: Dict) -> Issue:
        """이슈 해결"""
        issue_id = validated_data["issue_id"]

        with db_session() as session:
            issue = IssueService.safe_get_by_id(
                session, Issue, issue_id, "이슈를 찾을 수 없습니다."
            )

            if issue.resolved:
                raise ValueError("이미 해결된 이슈입니다.")

            issue.resolved = True
            return issue

    @staticmethod
    def get_issue_comments(issue_id: int) -> List[IssueComment]:
        """특정 이슈에 대한 댓글 목록 조회"""
        with db_session_read_only() as session:
            # 이슈 존재 확인
            IssueService.safe_get_by_id(
                session, Issue, issue_id, "이슈를 찾을 수 없습니다."
            )

            # 댓글 조회
            comments = (
                session.query(IssueComment)
                .filter(IssueComment.issue_id == issue_id)
                .order_by(IssueComment.created_at.asc())
                .all()
            )

            return comments

    @staticmethod
    def get_issue_by_id(issue_id: int) -> Issue:
        """ID로 이슈 조회"""
        with db_session_read_only() as session:
            return IssueService.safe_get_by_id(
                session, Issue, issue_id, "이슈를 찾을 수 없습니다."
            )

    @staticmethod
    def get_issues_by_course(
        training_course: str, include_resolved: bool = False
    ) -> List[Issue]:
        """교육과정별 이슈 조회"""
        with db_session_read_only() as session:
            query = session.query(Issue).filter(Issue.training_course == training_course)

            if not include_resolved:
                query = query.filter(Issue.resolved == False)

            return query.order_by(Issue.created_at.desc()).all()

    @staticmethod
    def update_issue(issue_id: int, update_data: Dict) -> Issue:
        """이슈 정보 업데이트"""
        with db_session() as session:
            issue = IssueService.safe_get_by_id(
                session, Issue, issue_id, "이슈를 찾을 수 없습니다."
            )

            # 업데이트할 필드들 적용
            allowed_fields = ["content", "training_course", "username"]
            for field, value in update_data.items():
                if field in allowed_fields and hasattr(issue, field):
                    setattr(issue, field, value)

            return issue

    @staticmethod
    def delete_comment(comment_id: int) -> None:
        """댓글 삭제"""
        with db_session() as session:
            comment = IssueService.safe_get_by_id(
                session, IssueComment, comment_id, "댓글을 찾을 수 없습니다."
            )
            session.delete(comment)
