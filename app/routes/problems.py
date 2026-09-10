from flask import Blueprint, abort, redirect, render_template, url_for

from app.db import get_db
from app.services.attempt_service import (
    DEMO_LEARNER_ID,
    AttemptService,
    ProblemNotFoundError,
)
from app.repositories.sqlite_attempt_repository import SQLiteAttemptRepository
from app.repositories.sqlite_problem_repository import SQLiteProblemRepository


bp = Blueprint("problems", __name__, url_prefix="/problems")


@bp.route("/", strict_slashes=False)
def index():
    problems = SQLiteProblemRepository(get_db()).list_all()
    return render_template("problems/index.html", problems=problems)


@bp.route("/<slug>/attempts", methods=["POST"])
def create_attempt(slug):
    connection = get_db()
    service = AttemptService(
        SQLiteAttemptRepository(connection),
        SQLiteProblemRepository(connection),
    )
    try:
        attempt = service.create_draft(slug, DEMO_LEARNER_ID)
    except ProblemNotFoundError:
        abort(404)
    return redirect(url_for("attempts.edit", attempt_id=attempt.id))


@bp.route("/<slug>")
def detail(slug):
    problem = SQLiteProblemRepository(get_db()).get_by_slug(slug)
    if problem is None:
        abort(404)
    return render_template("problems/detail.html", problem=problem)