from app.db import get_db
from app.models.enums import AttemptStatus
from app.repositories.sqlite_attempt_repository import SQLiteAttemptRepository
from app.repositories.sqlite_problem_repository import SQLiteProblemRepository
from app.services.attempt_service import DEMO_LEARNER_ID
from app.services.attempt_service import AttemptService
from app.services.evaluation_service import EvaluationService, PlaceholderEvaluator

from tests.test_evaluation_workflow import FailingEvaluator, valid_design


def create_saved_attempt(client, slug="clinic-queue-management", attempt_id=1):
    created = client.post(f"/problems/{slug}/attempts")
    assert created.status_code == 302
    saved = client.post(f"/attempts/{attempt_id}/save", data=valid_design())
    assert saved.status_code == 302


def test_unknown_submit_and_retry_attempts_return_not_found(client):
    assert client.post("/attempts/999/submit").status_code == 404
    assert client.post("/attempts/999/retry-evaluation").status_code == 404


def test_unknown_learner_cannot_load_attempt_or_submission(app, client):
    create_saved_attempt(client)
    with app.app_context():
        repository = SQLiteAttemptRepository(get_db())
        problems = SQLiteProblemRepository(get_db())
        service = AttemptService(repository, problems)

        assert repository.get_attempt(1, "another-learner") is None
        assert service.load_for_learner(1, "another-learner") is None


def test_successful_attempt_cannot_be_saved_or_retried_again(client, app):
    create_saved_attempt(client)
    assert client.post("/attempts/1/submit").status_code == 302

    save_again = client.post("/attempts/1/save", data=valid_design())
    retry_again = client.post("/attempts/1/retry-evaluation")

    assert save_again.status_code == 302
    assert retry_again.status_code == 302
    with app.app_context():
        status = get_db().execute(
            "SELECT status FROM attempts WHERE id = 1"
        ).fetchone()["status"]
        evaluation_count = get_db().execute(
            "SELECT COUNT(*) FROM evaluations WHERE attempt_id = 1"
        ).fetchone()[0]
    assert status == AttemptStatus.FEEDBACK_READY.value
    assert evaluation_count == 1


def test_failed_attempt_remains_visible_in_history(client, app):
    create_saved_attempt(client)
    with app.app_context():
        repository = SQLiteAttemptRepository(get_db())
        problems = SQLiteProblemRepository(get_db())
        try:
            EvaluationService(repository, problems, FailingEvaluator()).submit_attempt(
                1, DEMO_LEARNER_ID
            )
        except Exception:
            pass

    history = client.get("/history")

    assert history.status_code == 200
    assert b"Evaluation Failed" in history.data
    assert b"View Feedback" in history.data


def test_feedback_escapes_learner_html_like_content(client):
    create_saved_attempt(client)
    special = valid_design()
    special["classes_text"] = "<script>alert('x')</script> Patient and QueueToken"
    special["relationships_text"] = (
        "QueueService creates QueueToken and assigns Doctor through a safe workflow "
        "with enough detail to satisfy the submission length requirement."
    )
    client.post("/attempts/1/save", data=special)
    client.post("/attempts/1/submit")

    feedback = client.get("/attempts/1/feedback")

    assert b"&lt;script&gt;alert(&#39;x&#39;)&lt;/script&gt;" in feedback.data
    assert b"<script>alert('x')</script>" not in feedback.data