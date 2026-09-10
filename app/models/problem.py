import json
import sqlite3
from dataclasses import dataclass, field
from typing import Mapping


@dataclass
class PracticeProblem:
    id: int | None
    slug: str
    title: str
    difficulty: str
    summary: str
    description: str
    requirements: list[str]
    constraints: list[str]
    rubric: dict[str, int]
    criteria: dict[str, object] = field(default_factory=dict)


def practice_problem_from_row(row: sqlite3.Row) -> PracticeProblem:
    rubric_data = json.loads(row["rubric_json"])
    if "scores" in rubric_data:
        rubric = rubric_data["scores"]
        criteria = rubric_data.get("criteria", {})
    else:
        rubric = rubric_data
        criteria = {}
    return PracticeProblem(
        id=row["id"],
        slug=row["slug"],
        title=row["title"],
        difficulty=row["difficulty"],
        summary=row["summary"],
        description=row["description"],
        requirements=json.loads(row["requirements_json"]),
        constraints=json.loads(row["constraints_json"]),
        rubric=rubric,
        criteria=criteria,
    )


def practice_problem_json_fields(problem: PracticeProblem) -> Mapping[str, str]:
    """Return JSON-backed fields in the shape expected by SQLite repositories."""
    return {
        "requirements_json": json.dumps(problem.requirements),
        "constraints_json": json.dumps(problem.constraints),
        "rubric_json": json.dumps(
            {"scores": problem.rubric, "criteria": problem.criteria}
        ),
    }