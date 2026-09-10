from app.db import get_db
from app.models.enums import AttemptStatus
from app.repositories.sqlite_attempt_repository import SQLiteAttemptRepository
from app.repositories.sqlite_problem_repository import SQLiteProblemRepository
from app.services.attempt_service import DEMO_LEARNER_ID, AttemptService
from app.services.evaluation_service import EvaluationService, PlaceholderEvaluator

from tests.test_evaluation_workflow import FailingEvaluator, valid_design


def create_saved_attempt(client):
    created = client.post("/problems/clinic-queue-management/attempts")
    assert created.status_code == 302
    saved = client.post("/attempts/1/save", data=valid_design())
    assert saved.status_code == 302


def test_failure_preserves_submission_and_exposes_retry(client, app):
    create_saved_attempt(client)
    with app.app_context():
        service = EvaluationService(
            SQLiteAttemptRepository(get_db()),
            SQLiteProblemRepository(get_db()),
            FailingEvaluator(),
        )
        try:
            service.submit_attempt(1, DEMO_LEARNER_ID)
        except Exception:
            pass
        attempt = service.attempt_repository.get_attempt(1, DEMO_LEARNER_ID)
        submission = service.attempt_repository.get_submission(1)
        failure = service.attempt_repository.get_evaluation(1)

    feedback = client.get("/attempts/1/feedback")
    assert attempt.status is AttemptStatus.EVALUATION_FAILED
    assert submission.classes_text == valid_design()["classes_text"]
    assert failure.error_message == "We could not evaluate this attempt. Please try again."
    assert b"Evaluation failed" in feedback.data
    assert b"Retry Evaluation" in feedback.data


def test_retry_reuses_same_attempt_and_replaces_failure(client, app):
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

        before = repository.get_submission(1)
        attempt, result = EvaluationService(
            repository, problems, PlaceholderEvaluator()
        ).retry_evaluation(1, DEMO_LEARNER_ID)
        after = repository.get_submission(1)
        evaluation_count = get_db().execute(
            "SELECT COUNT(*) FROM evaluations WHERE attempt_id = 1"
        ).fetchone()[0]

    feedback = client.get("/attempts/1/feedback")
    assert attempt.id == 1
    assert attempt.status is AttemptStatus.FEEDBACK_READY
    assert result.overall_score == 60
    assert before == after
    assert evaluation_count == 1
    assert b"Overall score" in feedback.data
    assert b"Retry Evaluation" not in feedback.data


def test_attempt_service_rejects_editing_after_submit(app, client):
    create_saved_attempt(client)
    client.post("/attempts/1/submit")
    with app.app_context():
        service = AttemptService(
            SQLiteAttemptRepository(get_db()),
            SQLiteProblemRepository(get_db()),
        )
        try:
            service.save_draft(1, DEMO_LEARNER_ID, valid_design())
        except Exception as error:
            assert error.args == (1,)
        else:
            raise AssertionError("submitted attempts must not be editable")