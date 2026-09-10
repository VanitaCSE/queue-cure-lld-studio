from abc import ABC, abstractmethod

from app.models.attempt import Attempt
from app.models.evaluation import EvaluationResult
from app.models.submission import Submission


class AttemptRepository(ABC):
    @abstractmethod
    def create_attempt(self, attempt: Attempt, submission: Submission) -> Attempt:
        raise NotImplementedError

    @abstractmethod
    def get_attempt(self, attempt_id: int, learner_id: str) -> Attempt | None:
        raise NotImplementedError

    @abstractmethod
    def get_submission(self, attempt_id: int) -> Submission | None:
        raise NotImplementedError

    @abstractmethod
    def save_submission(self, submission: Submission) -> None:
        raise NotImplementedError

    @abstractmethod
    def update_attempt(self, attempt: Attempt) -> None:
        raise NotImplementedError

    @abstractmethod
    def update_attempt_status(
        self,
        attempt_id: int,
        learner_id: str,
        status,
        submitted_at: str | None = None,
    ) -> Attempt:
        raise NotImplementedError

    @abstractmethod
    def list_attempts_for_learner(self, learner_id: str) -> list[Attempt]:
        raise NotImplementedError

    @abstractmethod
    def save_evaluation(self, result: EvaluationResult) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_evaluation(self, attempt_id: int) -> EvaluationResult | None:
        raise NotImplementedError