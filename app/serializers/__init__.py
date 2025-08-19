# Serializers module
"""
모든 Serializer 클래스들을 한 곳에서 import할 수 있도록 하는 모듈
"""

# Base serializers
from .base import Serializer, ResponseSerializer

# Domain serializers
from .user import UserSerializer
from .attendance import AttendanceSerializer
from .issue import IssueSerializer
from .notice import NoticeSerializer
from .task import TaskSerializer
from .unchecked import UncheckedSerializer
from .training import TrainingSerializer
from .notification import NotificationSerializer
from .admin import AdminSerializer

# Helper functions
from .helpers import (
    json_response,
    error_json_response,
    pagination_json_response,
    handle_serialization_errors,
)

__all__ = [
    # Base classes
    "Serializer",
    "ResponseSerializer",
    # Domain serializers
    "UserSerializer",
    "AttendanceSerializer",
    "IssueSerializer",
    "NoticeSerializer",
    "TaskSerializer",
    "UncheckedSerializer",
    "TrainingSerializer",
    "NotificationSerializer",
    "AdminSerializer",
    # Helper functions
    "json_response",
    "error_json_response",
    "pagination_json_response",
    "handle_serialization_errors",
]
