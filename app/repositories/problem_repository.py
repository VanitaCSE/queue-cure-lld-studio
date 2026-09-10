from abc import ABC, abstractmethod

from app.models.problem import PracticeProblem


class ProblemRepository(ABC):
    @abstractmethod
    def get_by_slug(self, slug: str) -> PracticeProblem | None:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> list[PracticeProblem]:
        raise NotImplementedError

    @abstractmethod
    def seed_problem(self, problem: PracticeProblem) -> None:
        raise NotImplementedError