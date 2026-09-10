import sqlite3
from dataclasses import dataclass


@dataclass
class Submission:
    id: int | None
    attempt_id: int
    classes_text: str
    relationships_text: str
    extensibility_text: str
    tradeoffs_text: str
    diagram_text: str


def submission_from_row(row: sqlite3.Row) -> Submission:
    return Submission(
        id=row["id"],
        attempt_id=row["attempt_id"],
        classes_text=row["classes_text"],
        relationships_text=row["relationships_text"],
        extensibility_text=row["extensibility_text"],
        tradeoffs_text=row["tradeoffs_text"],
        diagram_text=row["diagram_text"],
    )