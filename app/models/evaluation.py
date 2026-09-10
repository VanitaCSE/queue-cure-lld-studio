import json
import sqlite3
from dataclasses import dataclass

from app.models.feedback import (
    FeedbackFinding,
    feedback_finding_from_json,
    feedback_finding_to_json,
)


@dataclass
class EvaluationResult:
    id: int | None
    attempt_id: int
    evaluator_name: str
    overall_score: int | None
    category_scores: dict[str, int]
    strengths: list[str]
    findings: list[FeedbackFinding]
    recommendations: list[str]
    error_message: str | None
    created_at: str


def evaluation_result_from_row(row: sqlite3.Row) -> EvaluationResult:
    findings_data = json.loads(row["findings_json"] or "[]")
    return EvaluationResult(
        id=row["id"],
        attempt_id=row["attempt_id"],
        evaluator_name=row["evaluator_name"],
        overall_score=row["overall_score"],
        category_scores=json.loads(row["category_scores_json"] or "{}"),
        strengths=json.loads(row["strengths_json"] or "[]"),
        findings=[feedback_finding_from_json(item) for item in findings_data],
        recommendations=json.loads(row["recommendations_json"] or "[]"),
        error_message=row["error_message"],
        created_at=row["created_at"],
    )


def evaluation_result_json_fields(result: EvaluationResult) -> dict[str, str]:
    return {
        "category_scores_json": json.dumps(result.category_scores),
        "strengths_json": json.dumps(result.strengths),
        "findings_json": json.dumps(
            [feedback_finding_to_json(finding) for finding in result.findings]
        ),
        "recommendations_json": json.dumps(result.recommendations),
    }