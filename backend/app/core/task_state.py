from enum import StrEnum


class TaskStatus(StrEnum):
    CREATED = "created"
    REQUIREMENT_PARSED = "requirement_parsed"
    OUTLINE_GENERATED = "outline_generated"
    DRAFT_GENERATED = "draft_generated"
    REVISING = "revising"
    REVISED = "revised"
    EXPORTED = "exported"
    FAILED = "failed"


ALLOWED_TRANSITIONS = {
    TaskStatus.CREATED: {
        TaskStatus.REQUIREMENT_PARSED,
        TaskStatus.FAILED,
    },
    TaskStatus.REQUIREMENT_PARSED: {
        TaskStatus.OUTLINE_GENERATED,
        TaskStatus.FAILED,
    },
    TaskStatus.OUTLINE_GENERATED: {
        TaskStatus.DRAFT_GENERATED,
        TaskStatus.FAILED,
    },
    TaskStatus.DRAFT_GENERATED: {
        TaskStatus.REVISING,
        TaskStatus.EXPORTED,
        TaskStatus.FAILED,
    },
    TaskStatus.REVISING: {
        TaskStatus.REVISED,
        TaskStatus.FAILED,
    },
    TaskStatus.REVISED: {
        TaskStatus.REVISING,
        TaskStatus.EXPORTED,
        TaskStatus.FAILED,
    },
    TaskStatus.EXPORTED: set(),
    TaskStatus.FAILED: set(),
}


def can_transition(current: str, target: str) -> bool:
    current_status = TaskStatus(current)
    target_status = TaskStatus(target)
    if current_status == target_status:
        return True
    return target_status in ALLOWED_TRANSITIONS[current_status]


def ensure_transition(current: str, target: str) -> None:
    if not can_transition(current, target):
        raise ValueError(f"Invalid task status transition: {current} -> {target}")

