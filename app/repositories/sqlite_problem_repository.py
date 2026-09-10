import sqlite3

from app.models.problem import (
    PracticeProblem,
    practice_problem_from_row,
    practice_problem_json_fields,
)
from app.repositories.problem_repository import ProblemRepository


class SQLiteProblemRepository(ProblemRepository):
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def get_by_slug(self, slug: str) -> PracticeProblem | None:
        row = self.connection.execute(
            "SELECT * FROM problems WHERE slug = ?", (slug,)
        ).fetchone()
        return practice_problem_from_row(row) if row is not None else None

    def list_all(self) -> list[PracticeProblem]:
        rows = self.connection.execute(
            "SELECT * FROM problems ORDER BY id"
        ).fetchall()
        return [practice_problem_from_row(row) for row in rows]

    def seed_problem(self, problem: PracticeProblem) -> None:
        json_fields = practice_problem_json_fields(problem)
        self.connection.execute(
            """
            INSERT INTO problems (
                slug,
                title,
                difficulty,
                summary,
                description,
                requirements_json,
                constraints_json,
                rubric_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                title = excluded.title,
                difficulty = excluded.difficulty,
                summary = excluded.summary,
                description = excluded.description,
                requirements_json = excluded.requirements_json,
                constraints_json = excluded.constraints_json,
                rubric_json = excluded.rubric_json
            """,
            (
                problem.slug,
                problem.title,
                problem.difficulty,
                problem.summary,
                problem.description,
                json_fields["requirements_json"],
                json_fields["constraints_json"],
                json_fields["rubric_json"],
            ),
        )