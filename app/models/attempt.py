import sqlite3
from dataclasses import dataclass

from app.models.enums import AttemptStatus


@dataclass
class Attempt:
    id: int | None
    learner_id: str
    problem_id: int
    status: AttemptStatus
    created_at: str
    updated_at: str
    submitted_at: str | None


def attempt_from_row(row: sqlite3.Row) -> Attempt:
    return Attempt(
        id=row["id"],
        learner_id=row["learner_id"],
        problem_id=row["problem_id"],
        status=AttemptStatus(row["status"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        submitted_at=row["submitted_at"],
    )