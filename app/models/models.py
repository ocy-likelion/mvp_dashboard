from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Date,
    Time,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# 한국 시간대 설정
KST = ZoneInfo("Asia/Seoul")


def kst_now():
    """한국 시간으로 현재 시간을 반환하는 함수"""
    return datetime.now(KST)


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(Text, nullable=False)
    password = Column(Text, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=kst_now)
    last_login = Column(DateTime)


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    instructor = Column(String(100))
    instructor_name = Column(String(100))
    training_course = Column(String(255))
    check_in_time = Column(Time)
    check_out_time = Column(Time)
    daily_log = Column(Boolean)


class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    training_course = Column(String(255))
    username = Column(String(100))
    created_by = Column(String(100))
    date = Column(Date)
    created_at = Column(DateTime, default=kst_now)
    resolved = Column(Boolean, default=False)

    # Relationships
    comments = relationship("IssueComment", back_populates="issue")


class IssueComment(Base):
    __tablename__ = "issue_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False)
    comment = Column(Text, nullable=False)
    created_by = Column(String(100))
    created_at = Column(DateTime, default=kst_now)

    # Relationships
    issue = relationship("Issue", back_populates="comments")


class Notice(Base):
    __tablename__ = "notices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(50))
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    date = Column(DateTime, default=kst_now)
    created_by = Column(String(100))
    modified_by = Column(String(100))
    is_deleted = Column(Boolean, default=False)

    # Relationships
    reads = relationship("NoticeRead", back_populates="notice")


class NoticeRead(Base):
    __tablename__ = "notice_reads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    notice_id = Column(Integer, ForeignKey("notices.id"), nullable=False)
    username = Column(String(100), nullable=False)
    read_at = Column(DateTime, default=kst_now)

    # Relationships
    notice = relationship("Notice", back_populates="reads")


class TaskItem(Base):
    __tablename__ = "task_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_name = Column(Text, nullable=False)
    task_period = Column(String(10))
    task_category = Column(Text)
    guide = Column(Text)
    due = Column(Integer)

    # Relationships
    checklists = relationship("TaskChecklist", back_populates="task_item")
    unchecked_descriptions = relationship(
        "UncheckedDescription", back_populates="task_item"
    )


class TaskChecklist(Base):
    __tablename__ = "task_checklist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("task_items.id"), nullable=False)
    training_course = Column(Text, nullable=False)
    is_checked = Column(Boolean, default=False)
    checked_date = Column(DateTime, default=kst_now)
    username = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    task_item = relationship("TaskItem", back_populates="checklists")


class UncheckedComment(Base):
    __tablename__ = "unchecked_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    unchecked_id = Column(
        Integer, ForeignKey("unchecked_descriptions.id"), nullable=False
    )
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime, default=kst_now)
    user_id = Column(Integer, ForeignKey("users.id"))
    username = Column(String(255))
    created_by = Column(String(100))

    # Relationships
    unchecked_description = relationship(
        "UncheckedDescription", back_populates="comments"
    )


class UncheckedDescription(Base):
    __tablename__ = "unchecked_descriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=kst_now)
    training_course = Column(String(255))
    resolved = Column(Boolean, default=False)
    user_id = Column(Integer)  # FK가 명시되지 않음
    username = Column(String(255))
    action_plan = Column(Text)
    task_id = Column(Integer, ForeignKey("task_items.id"))
    created_by = Column(String(100))

    # Relationships
    comments = relationship("UncheckedComment", back_populates="unchecked_description")
    task_item = relationship("TaskItem", back_populates="unchecked_descriptions")


class TrainingInfo(Base):
    __tablename__ = "training_info"

    id = Column(Integer, primary_key=True, autoincrement=True)
    training_course = Column(String(255), nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)
    dept = Column(String(100))
    manager_name = Column(String(255))
    created_at = Column(DateTime, default=kst_now)


class UserLastCheck(Base):
    __tablename__ = "user_last_checks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False)
    last_notice_check = Column(DateTime)
    last_issue_check = Column(DateTime)
    last_comment_check = Column(DateTime)
