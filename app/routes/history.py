from flask import Blueprint, render_template

from app.db import get_db
from app.repositories.sqlite_attempt_repository import SQLiteAttemptRepository
from app.repositories.sqlite_problem_repository import SQLiteProblemRepository
from app.services.attempt_service import DEMO_LEARNER_ID

bp = Blueprint("history", __name__)


@bp.route("/history")
def index():
    connection = get_db()
    attempts = SQLiteAttemptRepository(connection).list_attempts_for_learner(
        DEMO_LEARNER_ID
    )
    problems = SQLiteProblemRepository(connection).list_all()
    problems_by_id = {problem.id: problem for problem in problems}
    return render_template(
        "attempts/history.html",
        attempts=attempts,
        problems_by_id=problems_by_id,
        evaluations={
            attempt.id: SQLiteAttemptRepository(connection).get_evaluation(attempt.id)
            for attempt in attempts
        },
    )