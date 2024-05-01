from enum import Enum


class SubmissionStatementState(str, Enum):
    MISSING = "MISSING"
    TOO_SHORT = "TOO_SHORT"
    VALID = "VALID"
