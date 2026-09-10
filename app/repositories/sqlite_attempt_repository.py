import sqlite3

from app.models.attempt import Attempt, attempt_from_row
from app.models.enums import AttemptStatus
from app.models.evaluation import (
    EvaluationResult,
    evaluation_result_from_row,
    evaluation_result_json_fields,
)
from app.models.submission import Submission, submission_from_row
from app.repositories.attempt_repository import AttemptRepository


DEMO_LEARNER_ID = "demo-learner"


class SQLiteAttemptRepository(AttemptRepository):
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def create_attempt(self, attempt: Attempt, submission: Submission) -> Attempt:
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO attempts (
                    learner_id,
                    problem_id,
                    status,
                    created_at,
                    updated_at,
                    submitted_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    attempt.learner_id,
                    attempt.problem_id,
                    attempt.status.value,
                    attempt.created_at,
                    attempt.updated_at,
                    attempt.submitted_at,
                ),
            )
            attempt_id = cursor.lastrowid
            self.connection.execute(
                """
                INSERT INTO submissions (
                    attempt_id,
                    classes_text,
                    relationships_text,
                    extensibility_text,
                    tradeoffs_text,
                    diagram_text
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    attempt_id,
                    submission.classes_text,
                    submission.relationships_text,
                    submission.extensibility_text,
                    submission.tradeoffs_text,
                    submission.diagram_text,
                ),
            )

        row = self.connection.execute(
            "SELECT * FROM attempts WHERE id = ? AND learner_id = ?",
            (attempt_id, attempt.learner_id),
        ).fetchone()
        return attempt_from_row(row)

    def get_attempt(self, attempt_id: int, learner_id: str) -> Attempt | None:
        row = self.connection.execute(
            "SELECT * FROM attempts WHERE id = ? AND learner_id = ?",
            (attempt_id, learner_id),
        ).fetchone()
        return attempt_from_row(row) if row is not None else None

    def get_submission(self, attempt_id: int) -> Submission | None:
        row = self.connection.execute(
            """
            SELECT submissions.*
            FROM submissions
            JOIN attempts ON attempts.id = submissions.attempt_id
            WHERE submissions.attempt_id = ?
              AND attempts.learner_id = ?
            """,
            (attempt_id, DEMO_LEARNER_ID),
        ).fetchone()
        return submission_from_row(row) if row is not None else None

    def save_submission(self, submission: Submission) -> None:
        with self.connection:
            self.connection.execute(
                """
                UPDATE submissions
                SET classes_text = ?,
                    relationships_text = ?,
                    extensibility_text = ?,
                    tradeoffs_text = ?,
                    diagram_text = ?
                WHERE attempt_id = ?
                  AND EXISTS (
                      SELECT 1 FROM attempts
                      WHERE attempts.id = submissions.attempt_id
                        AND attempts.learner_id = ?
                  )
                """,
                (
                    submission.classes_text,
                    submission.relationships_text,
                    submission.extensibility_text,
                    submission.tradeoffs_text,
                    submission.diagram_text,
                    submission.attempt_id,
                    DEMO_LEARNER_ID,
                ),
            )

    def update_attempt(self, attempt: Attempt) -> None:
        with self.connection:
            self.connection.execute(
                """
                UPDATE attempts
                SET status = ?, updated_at = ?, submitted_at = ?
                WHERE id = ? AND learner_id = ?
                """,
                (
                    attempt.status.value,
                    attempt.updated_at,
                    attempt.submitted_at,
                    attempt.id,
                    attempt.learner_id,
                ),
            )

    def update_attempt_status(
        self,
        attempt_id: int,
        learner_id: str,
        status: AttemptStatus,
        submitted_at: str | None = None,
    ) -> Attempt:
        from app.services.attempt_service import utc_now_iso

        with self.connection:
            self.connection.execute(
                """
                UPDATE attempts
                SET status = ?, updated_at = ?, submitted_at = ?
                WHERE id = ? AND learner_id = ?
                """,
                (
                    status.value,
                    utc_now_iso(),
                    submitted_at,
                    attempt_id,
                    learner_id,
                ),
            )
        row = self.connection.execute(
            "SELECT * FROM attempts WHERE id = ? AND learner_id = ?",
            (attempt_id, learner_id),
        ).fetchone()
        if row is None:
            raise LookupError("Attempt not found for learner.")
        return attempt_from_row(row)

    def list_attempts_for_learner(self, learner_id: str) -> list[Attempt]:
        rows = self.connection.execute(
            """
            SELECT * FROM attempts
            WHERE learner_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (learner_id,),
        ).fetchall()
        return [attempt_from_row(row) for row in rows]

    def save_evaluation(self, result: EvaluationResult) -> None:
        json_fields = evaluation_result_json_fields(result)
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO evaluations (
                    attempt_id,
                    evaluator_name,
                    overall_score,
                    category_scores_json,
                    strengths_json,
                    findings_json,
                    recommendations_json,
                    error_message,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(attempt_id) DO UPDATE SET
                    evaluator_name = excluded.evaluator_name,
                    overall_score = excluded.overall_score,
                    category_scores_json = excluded.category_scores_json,
                    strengths_json = excluded.strengths_json,
                    findings_json = excluded.findings_json,
                    recommendations_json = excluded.recommendations_json,
                    error_message = excluded.error_message,
                    created_at = excluded.created_at
                """,
                (
                    result.attempt_id,
                    result.evaluator_name,
                    result.overall_score,
                    json_fields["category_scores_json"],
                    json_fields["strengths_json"],
                    json_fields["findings_json"],
                    json_fields["recommendations_json"],
                    result.error_message,
                    result.created_at,
                ),
            )

    def get_evaluation(self, attempt_id: int) -> EvaluationResult | None:
        row = self.connection.execute(
            """
            SELECT evaluations.*
            FROM evaluations
            JOIN attempts ON attempts.id = evaluations.attempt_id
            WHERE evaluations.attempt_id = ?
              AND attempts.learner_id = ?
            """,
            (attempt_id, DEMO_LEARNER_ID),
        ).fetchone()
        return evaluation_result_from_row(row) if row is not None else None