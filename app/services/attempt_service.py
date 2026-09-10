from datetime import datetime, timezone
import logging
from typing import Mapping

from app.models.attempt import Attempt
from app.models.enums import AttemptStatus
from app.models.submission import Submission
from app.repositories.attempt_repository import AttemptRepository
from app.repositories.problem_repository import ProblemRepository


DEMO_LEARNER_ID = "demo-learner"
MAX_TEXT_LENGTH = 10_000
SUBMISSION_FIELDS = (
    "classes_text",
    "relationships_text",
    "extensibility_text",
    "tradeoffs_text",
    "diagram_text",
)


class ProblemNotFoundError(Exception):
    pass


class AttemptNotFoundError(Exception):
    pass


class DraftValidationError(Exception):
    def __init__(self, errors: dict[str, str], submission: Submission):
        super().__init__("Draft submission contains invalid fields.")
        self.errors = errors
        self.submission = submission


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class AttemptService:
    def __init__(
        self,
        attempt_repository: AttemptRepository,
        problem_repository: ProblemRepository,
    ):
        self.attempt_repository = attempt_repository
        self.problem_repository = problem_repository

    def create_draft(self, problem_slug: str, learner_id: str) -> Attempt:
        problem = self.problem_repository.get_by_slug(problem_slug)
        if problem is None:
            raise ProblemNotFoundError(problem_slug)

        timestamp = utc_now_iso()
        attempt = Attempt(
            id=None,
            learner_id=learner_id,
            problem_id=problem.id,
            status=AttemptStatus.DRAFT,
            created_at=timestamp,
            updated_at=timestamp,
            submitted_at=None,
        )
        blank_submission = Submission(
            id=None,
            attempt_id=0,
            classes_text="",
            relationships_text="",
            extensibility_text="",
            tradeoffs_text="",
            diagram_text="",
        )
        return self.attempt_repository.create_attempt(attempt, blank_submission)

    def load_for_learner(
        self, attempt_id: int, learner_id: str
    ) -> tuple[Attempt, Submission] | None:
        attempt = self.attempt_repository.get_attempt(attempt_id, learner_id)
        if attempt is None:
            return None
        submission = self.attempt_repository.get_submission(attempt_id)
        if submission is None:
            return None
        return attempt, submission

    def save_draft(
        self,
        attempt_id: int,
        learner_id: str,
        values: Mapping[str, object],
    ) -> Attempt:
        workspace = self.load_for_learner(attempt_id, learner_id)
        if workspace is None:
            raise AttemptNotFoundError(attempt_id)

        attempt, existing_submission = workspace
        if attempt.status is not AttemptStatus.DRAFT:
            raise AttemptNotFoundError(attempt_id)
        submission = self._submission_from_values(
            attempt_id, existing_submission.id, values
        )
        self.attempt_repository.save_submission(submission)
        attempt.updated_at = utc_now_iso()
        self.attempt_repository.update_attempt(attempt)
        return attempt

    def _submission_from_values(
        self,
        attempt_id: int,
        submission_id: int | None,
        values: Mapping[str, object],
    ) -> Submission:
        errors: dict[str, str] = {}
        text_values: dict[str, str] = {}

        for field in SUBMISSION_FIELDS:
            value = values.get(field, "")
            if not isinstance(value, str):
                errors[field] = "This field must contain text."
                text_values[field] = ""
            else:
                text_values[field] = value
                if len(value) > MAX_TEXT_LENGTH:
                    errors[field] = (
                        f"This field must be {MAX_TEXT_LENGTH:,} characters or fewer."
                    )

        submission = Submission(
            id=submission_id,
            attempt_id=attempt_id,
            classes_text=text_values["classes_text"],
            relationships_text=text_values["relationships_text"],
            extensibility_text=text_values["extensibility_text"],
            tradeoffs_text=text_values["tradeoffs_text"],
            diagram_text=text_values["diagram_text"],
        )
        if errors:
            raise DraftValidationError(errors, submission)
        return submission