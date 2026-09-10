import re
from datetime import datetime, timezone
from typing import Any

from app.evaluators.evaluator import Evaluator
from app.models.enums import FindingSeverity
from app.models.evaluation import EvaluationResult
from app.models.feedback import FeedbackFinding
from app.models.problem import PracticeProblem
from app.models.submission import Submission


CATEGORIES = (
    "Requirements coverage",
    "Responsibility design",
    "Extensibility and abstractions",
    "Relationships and workflow",
    "Edge cases and trade-offs",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class RuleBasedEvaluator(Evaluator):
    name = "rule-based-evaluator"

    def evaluate(self, problem: PracticeProblem, submission: Submission) -> EvaluationResult:
        texts = {
            "classes": self._normalize(submission.classes_text),
            "relationships": self._normalize(submission.relationships_text),
            "extensibility": self._normalize(submission.extensibility_text),
            "tradeoffs": self._normalize(submission.tradeoffs_text),
            "diagram": self._normalize(submission.diagram_text),
        }
        combined = " ".join(texts.values())
        criteria = problem.criteria or self._legacy_criteria()
        findings: list[FeedbackFinding] = []
        recommendations: list[str] = []

        scores = {
            "Requirements coverage": self._requirements_score(combined, criteria),
            "Responsibility design": self._responsibility_score(combined, criteria),
            "Extensibility and abstractions": self._extensibility_score(combined),
            "Relationships and workflow": self._relationships_score(texts["relationships"], criteria),
            "Edge cases and trade-offs": self._tradeoffs_score(texts, combined),
        }
        scores = {
            category: min(max(scores.get(category, 0), 0), problem.rubric.get(category, 0))
            for category in CATEGORIES
        }

        self._add_requirement_findings(combined, criteria, findings, recommendations)
        self._add_responsibility_findings(combined, criteria, findings, recommendations)
        self._add_relationship_findings(texts["relationships"], criteria, findings, recommendations)
        self._add_shared_findings(texts, combined, findings, recommendations)

        return EvaluationResult(
            id=None,
            attempt_id=0,
            evaluator_name=self.name,
            overall_score=min(max(sum(scores.values()), 0), 100),
            category_scores=scores,
            strengths=self._strengths(texts, combined, criteria)[:4],
            findings=findings,
            recommendations=recommendations[:3],
            error_message=None,
            created_at=utc_now_iso(),
        )

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"\s+", " ", value.casefold())

    @staticmethod
    def _has(text: str, *terms: str) -> bool:
        return any(term in text for term in terms)

    def _requirements_score(self, text: str, criteria: dict[str, Any]) -> int:
        return sum(
            item.get("points", 0)
            for item in criteria.get("requirements", [])
            if self._has(text, *item.get("terms", []))
        )

    def _responsibility_score(self, text: str, criteria: dict[str, Any]) -> int:
        concepts = criteria.get("responsibilities", {}).get("concepts", [])
        concept_count = sum(1 for concept in concepts if concept in text)
        responsibility_points = 5 if self._has(
            text,
            "responsibil",
            "stores",
            "owns",
            "tracks",
            "creates",
            "selects",
            "assigns",
            "sends",
            "updates",
            "coordinates",
        ) else 0
        separation_points = 4 if concept_count >= 3 else 0
        return concept_count * 4 + responsibility_points + separation_points

    def _extensibility_score(self, text: str) -> int:
        strategy = self._has(
            text,
            "strategy",
            "selection policy",
            "scheduling policy",
            "pricing policy",
            "fee policy",
            "policy",
        )
        abstraction = self._has(
            text,
            "interface",
            "abstract",
            "notification channel",
            "notification service",
            "repository",
        )
        implementations = self._has(
            text, "sms", "email", "in-app", "dashboard", "push", "hourly", "vehicle-specific"
        )
        return (8 if strategy else 0) + (6 if abstraction else 0) + (3 if implementations else 0)

    def _relationships_score(self, relationships: str, criteria: dict[str, Any]) -> int:
        checks = criteria.get("relationships", {}).get("checks", [])
        return sum(4 for terms in checks if self._has(relationships, *terms))

    def _tradeoffs_score(self, texts: dict[str, str], combined: str) -> int:
        score = 5 if len(texts["tradeoffs"].strip()) >= 30 else 0
        score += 3 if self._has(combined, "no show", "no-show", "noshow", "cancel", "cancellation", "no suitable") else 0
        score += 3 if self._has(combined, "unavailable", "unavailability", "doctor availability", "spot availability") else 0
        score += 2 if self._has(combined, "one active token", "one active ticket", "one spot", "active token", "active ticket") else 0
        score += 2 if self._has(combined, "priority", "fifo", "first in first out", "pricing", "compatibility") else 0
        return score

    def _add_requirement_findings(self, text, criteria, findings, recommendations):
        for item in criteria.get("requirements", []):
            if self._has(text, *item.get("terms", [])) or not item.get("where"):
                continue
            self._add(
                findings,
                recommendations,
                "Requirements coverage",
                FindingSeverity.IMPORTANT if item.get("points", 0) >= 3 else FindingSeverity.WARNING,
                item.get("title", "A required concept is not explained"),
                item["where"],
                item.get("why", "The design does not yet explain this important requirement."),
                item.get("how_to_improve", "Consider describing the concept and its responsibility."),
                item.get("recommendation", "Explain this required concept in the design."),
            )

    def _add_responsibility_findings(self, text, criteria, findings, recommendations):
        manager_terms = criteria.get("responsibilities", {}).get("manager_terms", ["queue service", "queue manager"])
        if any(term in text for term in manager_terms):
            responsibilities = ("creat", "register", "select", "assign", "notif", "send", "status", "state", "persist", "store", "repository", "database")
            if sum(1 for term in responsibilities if term in text) >= 4:
                self._add(
                    findings,
                    recommendations,
                    "Responsibility design",
                    FindingSeverity.IMPORTANT,
                    "Queue coordination may have too many responsibilities",
                    "Classes and responsibilities",
                    "A single coordinating service that creates objects, selects resources, assigns work, sends notifications, and persists data can become difficult to test and modify.",
                    "Consider separating selection, assignment, notification, and persistence behind focused services or interfaces.",
                    "Split unrelated responsibilities out of the coordinating service.",
                )
        concepts = criteria.get("responsibilities", {}).get("concepts", [])
        if sum(1 for concept in concepts if concept in text) < 3:
            self._add(
                findings,
                recommendations,
                "Responsibility design",
                FindingSeverity.WARNING,
                "Core responsibilities are not sufficiently separated",
                "Classes and responsibilities",
                "The design does not yet show enough separate objects to make ownership of domain data and workflow behavior clear.",
                "Describe separate responsibilities for the main domain objects and a coordinating service.",
                "Separate core domain responsibilities into focused objects.",
            )

    def _add_relationship_findings(self, relationships, criteria, findings, recommendations):
        checks = criteria.get("relationships", {}).get("checks", [])
        if relationships.strip() and sum(1 for terms in checks if self._has(relationships, *terms)) < 2:
            self._add(
                findings,
                recommendations,
                "Relationships and workflow",
                FindingSeverity.WARNING,
                "Object relationships and workflow are too vague",
                "Relationships and main workflow",
                "An LLD design needs to show which object owns data, which object coordinates actions, and how the main use case moves between objects.",
                "Describe the main flow between the domain objects and coordinating services.",
                "Describe the main object interaction flow.",
            )

    def _add_shared_findings(self, texts, combined, findings, recommendations):
        if len(texts["tradeoffs"].strip()) < 30:
            self._add(
                findings,
                recommendations,
                "Edge cases and trade-offs",
                FindingSeverity.WARNING,
                "Assumptions and trade-offs are not explained",
                "Assumptions and trade-offs",
                "LLD decisions depend on business rules. Without stated assumptions, reviewers cannot tell why policies and responsibilities were chosen.",
                "State assumptions, edge cases, and the trade-offs behind important policies.",
                "Describe assumptions, edge cases, and trade-offs.",
            )
        if not self._has(combined, "unavailable", "unavailability", "doctor availability", "spot availability", "no suitable"):
            self._add(
                findings,
                recommendations,
                "Edge cases and trade-offs",
                FindingSeverity.WARNING,
                "Availability edge case is not addressed",
                "Assumptions and trade-offs",
                "A resource may become unavailable or no suitable resource may exist. The design needs a consistent rule for that case.",
                "Describe whether the request waits, is rejected, or is handled by another suitable resource.",
                "Describe unavailable-resource handling.",
            )
        if not self._has(combined, "strategy", "policy", "interface", "abstract", "repository"):
            self._add(
                findings,
                recommendations,
                "Extensibility and abstractions",
                FindingSeverity.WARNING,
                "Changeable behavior is not isolated",
                "Interfaces and extensibility choices",
                "Policies may evolve. Hard-coding them into one service makes future changes more invasive.",
                "Consider an interface or strategy for a behavior likely to change.",
                "Describe an abstraction for a changeable policy.",
            )

    def _strengths(self, texts, combined, criteria):
        strengths = []
        concepts = criteria.get("responsibilities", {}).get("concepts", [])
        if sum(1 for concept in concepts if concept in combined) >= 3:
            strengths.append("You separated several domain concepts, which makes ownership and responsibilities easier to review.")
        if self._has(combined, "strategy", "policy"):
            strengths.append("You described a changeable policy or strategy, which makes future rule changes easier.")
        if self._has(combined, "interface", "abstract", "repository"):
            strengths.append("You described an abstraction that can isolate dependencies or future implementations.")
        if len(texts["tradeoffs"].strip()) >= 30:
            strengths.append("You stated assumptions or trade-offs, which makes the design rationale easier to review.")
        if sum(1 for term in ("creates", "uses", "assign", "owns", "updates", "triggers", "releases") if term in texts["relationships"]) >= 2:
            strengths.append("You described object interactions rather than listing classes in isolation.")
        return strengths

    @staticmethod
    def _add(findings, recommendations, category, severity, title, where, why, how_to_improve, recommendation):
        if any(f.title == title for f in findings):
            return
        findings.append(FeedbackFinding(category, severity, title, where, why, how_to_improve))
        if recommendation not in recommendations:
            recommendations.append(recommendation)

    @staticmethod
    def _legacy_criteria() -> dict[str, object]:
        return {"requirements": [], "responsibilities": {}, "relationships": {"checks": []}}
