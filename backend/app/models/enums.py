from enum import Enum

class CaseStatus(str, Enum):
    UNRESOLVED = "UNRESOLVED"
    AT_RISK = "AT_RISK"
    BLOCKED = "BLOCKED"
    EXCEPTION = "EXCEPTION"
    OVERDUE = "OVERDUE"
    RESOLVED = "RESOLVED"
    IN_PROGRESS = "IN_PROGRESS"

class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"

class ActionType(str, Enum):
    RESOLVE = "RESOLVE"
    REASSIGN = "REASSIGN"
    ESCALATE = "ESCALATE"

class WorkItemStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"

class CommitmentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    FULFILLED = "FULFILLED"
    BREACHED = "BREACHED"

class BlockerStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"

class ExceptionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"
