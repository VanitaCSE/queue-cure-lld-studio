from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app.db import get_db
from app.repositories.sqlite_attempt_repository import SQLiteAttemptRepository
from app.repositories.sqlite_problem_repository import SQLiteProblemRepository
from app.evaluators.rule_based_evaluator import RuleBasedEvaluator
from app.services.attempt_service import (
    DEMO_LEARNER_ID,
    AttemptNotFoundError,
    AttemptService,
    DraftValidationError,
)
from app.services.evaluation_service import (
    DEMO_LEARNER_ID as EVALUATION_LEARNER_ID,
    EvaluationFailedError,
    EvaluationNotFoundError,
    EvaluationService,
    EvaluationStateError,
    EvaluationValidationError,
)

bp = Blueprint("attempts", __name__, url_prefix="/attempts")


def get_attempt_service() -> AttemptService:
    connection = get_db()
    return AttemptService(
        SQLiteAttemptRepository(connection),
        SQLiteProblemRepository(connection),
    )


def get_problem_for_attempt(attempt):
    problems = get_attempt_service().problem_repository.list_all()
    return next((problem for problem in problems if problem.id == attempt.problem_id), None)


def get_evaluation_service() -> EvaluationService:
    connection = get_db()
    return EvaluationService(
        SQLiteAttemptRepository(connection),
        SQLiteProblemRepository(connection),
        RuleBasedEvaluator(),
    )


@bp.route("/<int:attempt_id>/edit")
def edit(attempt_id):
    service = get_attempt_service()
    workspace = service.load_for_learner(attempt_id, DEMO_LEARNER_ID)
    if workspace is None:
        abort(404)

    attempt, submission = workspace
    problem = get_problem_for_attempt(attempt)
    if problem is None:
        abort(404)
    return render_template(
        "attempts/form.html",
        attempt=attempt,
        submission=submission,
        problem=problem,
        errors={},
    )


@bp.route("/<int:attempt_id>/save", methods=["POST"])
def save(attempt_id):
    service = get_attempt_service()
    existing = service.load_for_learner(attempt_id, DEMO_LEARNER_ID)
    if existing is None:
        abort(404)
    if existing[0].status.value != "DRAFT":
        flash("Only draft attempts can be edited.", "warning")
        return redirect(url_for("attempts.detail", attempt_id=attempt_id))
    values = request.form.to_dict()
    try:
        service.save_draft(attempt_id, DEMO_LEARNER_ID, values)
    except AttemptNotFoundError:
        abort(404)
    except DraftValidationError as error:
        workspace = service.load_for_learner(attempt_id, DEMO_LEARNER_ID)
        if workspace is None:
            abort(404)
        attempt, _ = workspace
        problem = get_problem_for_attempt(attempt)
        if problem is None:
            abort(404)
        return render_template(
            "attempts/form.html",
            attempt=attempt,
            submission=error.submission,
            problem=problem,
            errors=error.errors,
        ), 400

    flash("Draft saved successfully.", "success")
    return redirect(url_for("attempts.edit", attempt_id=attempt_id))


@bp.route("/<int:attempt_id>")
def detail(attempt_id):
    service = get_attempt_service()
    workspace = service.load_for_learner(attempt_id, DEMO_LEARNER_ID)
    if workspace is None:
        abort(404)
    attempt, _ = workspace
    if attempt.status.value == "DRAFT":
        return redirect(url_for("attempts.edit", attempt_id=attempt_id))
    return redirect(url_for("attempts.feedback", attempt_id=attempt_id))


@bp.route("/<int:attempt_id>/submit", methods=["POST"])
def submit(attempt_id):
    service = get_evaluation_service()
    try:
        service.submit_attempt(attempt_id, EVALUATION_LEARNER_ID)
    except EvaluationNotFoundError:
        abort(404)
    except EvaluationValidationError as error:
        workspace = get_attempt_service().load_for_learner(
            attempt_id, DEMO_LEARNER_ID
        )
        if workspace is None:
            abort(404)
        attempt, _ = workspace
        problem = get_problem_for_attempt(attempt)
        return render_template(
            "attempts/form.html",
            attempt=attempt,
            submission=error.submission,
            problem=problem,
            errors=error.errors,
        ), 400
    except EvaluationStateError as error:
        flash(str(error), "warning")
        return redirect(url_for("attempts.detail", attempt_id=attempt_id))
    except EvaluationFailedError as error:
        flash(error.user_message, "danger")
        return redirect(url_for("attempts.feedback", attempt_id=attempt_id))

    flash("Design submitted successfully. Feedback is ready.", "success")
    return redirect(url_for("attempts.feedback", attempt_id=attempt_id))


@bp.route("/<int:attempt_id>/retry-evaluation", methods=["POST"])
def retry_evaluation(attempt_id):
    service = get_evaluation_service()
    try:
        service.retry_evaluation(attempt_id, EVALUATION_LEARNER_ID)
    except EvaluationNotFoundError:
        abort(404)
    except (EvaluationStateError, EvaluationFailedError) as error:
        flash(getattr(error, "user_message", str(error)), "danger")
        return redirect(url_for("attempts.feedback", attempt_id=attempt_id))
    return redirect(url_for("attempts.feedback", attempt_id=attempt_id))


@bp.route("/<int:attempt_id>/feedback")
def feedback(attempt_id):
    service = get_evaluation_service()
    try:
        attempt, submission, problem = service._load_context(
            attempt_id, EVALUATION_LEARNER_ID
        )
    except EvaluationNotFoundError:
        abort(404)
    evaluation = service.attempt_repository.get_evaluation(attempt_id)
    return render_template(
        "attempts/feedback.html",
        attempt=attempt,
        submission=submission,
        problem=problem,
        evaluation=evaluation,
        failure_message=(
            evaluation.error_message
            if evaluation and evaluation.error_message
            else None
        ),
    )