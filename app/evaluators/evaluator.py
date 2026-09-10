from typing import Protocol

from app.models.evaluation import EvaluationResult
from app.models.problem import PracticeProblem
from app.models.submission import Submission


class Evaluator(Protocol):
    def evaluate(
        self, problem: PracticeProblem, submission: Submission
    ) -> EvaluationResult:
        ...