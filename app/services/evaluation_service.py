from datetime import datetime, timezone
import logging
from app.models.attempt import Attempt
from app.models.enums import AttemptStatus, FindingSeverity
from app.models.evaluation import EvaluationResult
from app.models.feedback import FeedbackFinding
from app.models.problem import PracticeProblem
from app.models.submission import Submission
from app.repositories.attempt_repository import AttemptRepository
from app.repositories.problem_repository import ProblemRepository
from app.services.attempt_service import DEMO_LEARNER_ID
from app.evaluators.evaluator import Evaluator


GENERIC_EVALUATION_ERROR = "We could not evaluate this attempt. Please try again."
logger = logging.getLogger(__name__)


class EvaluationNotFoundError(Exception):
    pass


class EvaluationValidationError(Exception):
    def __init__(self, errors: dict[str, str], submission: Submission):
        super().__init__("Submission is not ready for evaluation.")
        self.errors = errors
        self.submission = submission


class EvaluationStateError(Exception):
    pass


class EvaluationFailedError(Exception):
    def __init__(self, message: str = GENERIC_EVALUATION_ERROR):
        super().__init__(message)
        self.user_message = message


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class PlaceholderEvaluator:
    name = "placeholder-evaluator"

    def evaluate(
        self, problem: PracticeProblem, submission: Submission
    ) -> EvaluationResult:
        return EvaluationResult(
            id=None,
            attempt_id=0,
            evaluator_name=self.name,
            overall_score=60,
            category_scores={
                "Requirements coverage": 12,
                "Responsibility design": 15,
                "Extensibility and abstractions": 12,
                "Relationships and workflow": 12,
                "Edge cases and trade-offs": 9,
            },
            strengths=[
                "Your design has been submitted and is ready for structured review."
            ],
            findings=[
                FeedbackFinding(
                    category="Prototype evaluation",
                    severity=FindingSeverity.INFO,
                    title="Detailed rule-based feedback will be available next.",
                    where="Whole submission",
                    why=(
                        "This prototype step validates the submission workflow before "
                        "applying detailed evaluation rules."
                    ),
                    how_to_improve=(
                        "Review your classes, relationships, extensibility choices, "
                        "and trade-offs before creating another attempt."
                    ),
                )
            ],
            recommendations=[
                "Use the feedback page to review your submitted design."
            ],
            error_message=None,
            created_at=utc_now_iso(),
        )


class EvaluationService:
    def __init__(
        self,
        attempt_repository: AttemptRepository,
        problem_repository: ProblemRepository,
        evaluator: Evaluator,
    ):
        self.attempt_repository = attempt_repository
        self.problem_repository = problem_repository
        self.evaluator = evaluator

    def submit_attempt(
        self, attempt_id: int, learner_id: str
    ) -> tuple[Attempt, EvaluationResult]:
        attempt, submission, problem = self._load_context(attempt_id, learner_id)
        if attempt.status is not AttemptStatus.DRAFT:
            raise EvaluationStateError("Only draft attempts can be submitted.")
        self._validate_final_submission(submission)

        self.attempt_repository.update_attempt_status(
            attempt_id, learner_id, AttemptStatus.SUBMITTED, utc_now_iso()
        )
        self.attempt_repository.update_attempt_status(
            attempt_id, learner_id, AttemptStatus.EVALUATING, utc_now_iso()
        )
        return self._evaluate_and_finish(attempt_id, learner_id, problem, submission)

    def retry_evaluation(
        self, attempt_id: int, learner_id: str
    ) -> tuple[Attempt, EvaluationResult]:
        attempt, submission, problem = self._load_context(attempt_id, learner_id)
        if attempt.status is not AttemptStatus.EVALUATION_FAILED:
            raise EvaluationStateError(
                "Only failed evaluations can be retried."
            )
        self.attempt_repository.update_attempt_status(
            attempt_id, learner_id, AttemptStatus.EVALUATING
        )
        return self._evaluate_and_finish(attempt_id, learner_id, problem, submission)

    def _evaluate_and_finish(
        self,
        attempt_id: int,
        learner_id: str,
        problem: PracticeProblem,
        submission: Submission,
    ) -> tuple[Attempt, EvaluationResult]:
        try:
            result = self.evaluator.evaluate(problem, submission)
            result.attempt_id = attempt_id
            self.attempt_repository.save_evaluation(result)
            attempt = self.attempt_repository.update_attempt_status(
                attempt_id, learner_id, AttemptStatus.FEEDBACK_READY
            )
            return attempt, result
        except Exception as error:
            logger.exception(
                "Evaluation failed for attempt_id=%s learner_id=%s",
                attempt_id,
                learner_id,
            )
            failure_result = EvaluationResult(
                id=None,
                attempt_id=attempt_id,
                evaluator_name=getattr(self.evaluator, "name", "evaluation-service"),
                overall_score=None,
                category_scores={},
                strengths=[],
                findings=[],
                recommendations=[],
                error_message=GENERIC_EVALUATION_ERROR,
                created_at=utc_now_iso(),
            )
            try:
                self.attempt_repository.save_evaluation(failure_result)
            except Exception:
                pass
            try:
                self.attempt_repository.update_attempt_status(
                    attempt_id, learner_id, AttemptStatus.EVALUATION_FAILED
                )
            except Exception:
                pass
            raise EvaluationFailedError() from error

    def _load_context(
        self, attempt_id: int, learner_id: str
    ) -> tuple[Attempt, Submission, PracticeProblem]:
        attempt = self.attempt_repository.get_attempt(attempt_id, learner_id)
        if attempt is None:
            raise EvaluationNotFoundError(attempt_id)
        submission = self.attempt_repository.get_submission(attempt_id)
        if submission is None:
            raise EvaluationNotFoundError(attempt_id)
        problem = next(
            (
                candidate
                for candidate in self.problem_repository.list_all()
                if candidate.id == attempt.problem_id
            ),
            None,
        )
        if problem is None:
            raise EvaluationNotFoundError(attempt_id)
        return attempt, submission, problem

    def _validate_final_submission(self, submission: Submission) -> None:
        errors: dict[str, str] = {}
        fields = (
            "classes_text",
            "relationships_text",
            "extensibility_text",
            "tradeoffs_text",
            "diagram_text",
        )
        for field in fields:
            value = getattr(submission, field)
            if not isinstance(value, str):
                errors[field] = "This field must contain text."
            elif len(value) > 10_000:
                errors[field] = "This field must be 10,000 characters or fewer."

        if not isinstance(submission.classes_text, str) or not submission.classes_text.strip():
            errors["classes_text"] = "Describe at least one class or responsibility."
        if not isinstance(submission.relationships_text, str) or not submission.relationships_text.strip():
            errors["relationships_text"] = "Describe the relationships and main workflow."
        if (
            isinstance(submission.classes_text, str)
            and isinstance(submission.relationships_text, str)
            and submission.classes_text.strip()
            and submission.relationships_text.strip()
            and len(submission.classes_text.strip())
            + len(submission.relationships_text.strip())
            < 120
        ):
            errors["relationships_text"] = (
                "Together, classes and relationships must contain at least 120 characters."
            )
        if errors:
            raise EvaluationValidationError(errors, submission)