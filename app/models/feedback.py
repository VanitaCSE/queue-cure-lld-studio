from dataclasses import dataclass

from app.models.enums import FindingSeverity


@dataclass
class FeedbackFinding:
    category: str
    severity: FindingSeverity
    title: str
    where: str
    why: str
    how_to_improve: str


def feedback_finding_from_json(data: dict[str, str]) -> FeedbackFinding:
    return FeedbackFinding(
        category=data["category"],
        severity=FindingSeverity(data["severity"]),
        title=data["title"],
        where=data["where"],
        why=data["why"],
        how_to_improve=data["how_to_improve"],
    )


def feedback_finding_to_json(finding: FeedbackFinding) -> dict[str, str]:
    return {
        "category": finding.category,
        "severity": finding.severity.value,
        "title": finding.title,
        "where": finding.where,
        "why": finding.why,
        "how_to_improve": finding.how_to_improve,
    }

