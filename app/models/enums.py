from enum import Enum


class AttemptStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    EVALUATING = "EVALUATING"
    FEEDBACK_READY = "FEEDBACK_READY"
    EVALUATION_FAILED = "EVALUATION_FAILED"


class FindingSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    IMPORTANT = "IMPORTANT"