from app.db import get_db
from app.models.enums import AttemptStatus
from app.repositories.sqlite_attempt_repository import SQLiteAttemptRepository
from app.repositories.sqlite_problem_repository import SQLiteProblemRepository
from app.services.evaluation_service import (
    GENERIC_EVALUATION_ERROR,
    EvaluationService,
    EvaluationStateError,
    PlaceholderEvaluator,
)
from app.evaluators.rule_based_evaluator import RuleBasedEvaluator
from app.services.attempt_service import DEMO_LEARNER_ID


FIELDS = (
    "classes_text",
    "relationships_text",
    "extensibility_text",
    "tradeoffs_text",
    "diagram_text",
)


def create_draft(client):
    response = client.post("/problems/clinic-queue-management/attempts")
    assert response.status_code == 302
    return 1


def valid_design():
    return {
        "classes_text": (
            "Patient stores identity and contact details. QueueToken owns its "
            "priority, lifecycle state, and timestamps. QueueService coordinates "
            "token creation and state transitions."
        ),
        "relationships_text": (
            "QueueService creates a QueueToken for a Patient and asks QueueStrategy "
            "to select the next suitable token. DoctorAssignmentService assigns it "
            "to an available Doctor and NotificationChannel reports changes."
        ),
        "extensibility_text": "QueueStrategy and NotificationChannel are interfaces.",
        "tradeoffs_text": "FIFO applies within each priority category.",
        "diagram_text": "classDiagram",
    }


def save_valid_design(client):
    create_draft(client)
    response = client.post("/attempts/1/save", data=valid_design())
    assert response.status_code == 302


def test_valid_submission_reaches_feedback_ready_and_creates_evaluation(client, app):
    save_valid_design(client)

    response = client.post("/attempts/1/submit")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/attempts/1/feedback")
    with app.app_context():
        attempt = get_db().execute("SELECT * FROM attempts WHERE id = 1").fetchone()
        evaluation = get_db().execute(
            "SELECT * FROM evaluations WHERE attempt_id = 1"
        ).fetchone()
    assert attempt["status"] == "FEEDBACK_READY"
    assert evaluation["evaluator_name"] == "rule-based-evaluator"
    assert evaluation["overall_score"] > 0


def test_empty_classes_is_rejected_and_stays_draft(client, app):
    create_draft(client)
    values = valid_design()
    values["classes_text"] = ""
    client.post("/attempts/1/save", data=values)

    response = client.post("/attempts/1/submit", data=values)

    assert response.status_code == 400
    assert b"Describe at least one class" in response.data
    with app.app_context():
        status = get_db().execute(
            "SELECT status FROM attempts WHERE id = 1"
        ).fetchone()["status"]
    assert status == "DRAFT"


def test_empty_relationships_is_rejected_and_stays_draft(client, app):
    create_draft(client)
    values = valid_design()
    values["relationships_text"] = ""
    client.post("/attempts/1/save", data=values)

    response = client.post("/attempts/1/submit", data=values)

    assert response.status_code == 400
    assert b"Describe the relationships" in response.data
    with app.app_context():
        status = get_db().execute(
            "SELECT status FROM attempts WHERE id = 1"
        ).fetchone()["status"]
    assert status == "DRAFT"


def test_short_core_design_is_rejected_and_stays_draft(client, app):
    create_draft(client)
    values = valid_design()
    values["classes_text"] = "Patient class."
    values["relationships_text"] = "Uses a service."
    client.post("/attempts/1/save", data=values)

    response = client.post("/attempts/1/submit", data=values)

    assert response.status_code == 400
    assert b"at least 120 characters" in response.data
    with app.app_context():
        status = get_db().execute(
            "SELECT status FROM attempts WHERE id = 1"
        ).fetchone()["status"]
    assert status == "DRAFT"


def test_submitting_non_draft_attempt_is_rejected(client, app):
    save_valid_design(client)
    client.post("/attempts/1/submit")

    response = client.post("/attempts/1/submit")

    assert response.status_code == 302
    with app.app_context():
        status = get_db().execute(
            "SELECT status FROM attempts WHERE id = 1"
        ).fetchone()["status"]
    assert status == "FEEDBACK_READY"


def test_feedback_page_displays_rule_based_evaluation(client):
    save_valid_design(client)
    client.post("/attempts/1/submit")

    response = client.get("/attempts/1/feedback")

    assert response.status_code == 200
    assert b"Overall score" in response.data
    assert b"Detailed rule-based feedback will be available next." not in response.data


def test_feedback_page_displays_scores_feedback_and_submission(client):
    save_valid_design(client)
    client.post("/attempts/1/submit")

    response = client.get("/attempts/1/feedback")

    assert response.status_code == 200
    for text in (
        b"Feedback available",
        b"Score:",
        b"/ 20",
        b"/ 25",
        b"What you did well",
        b"What could be improved",
        b"Next improvements",
        b"Your submission",
        b"Patient stores identity and contact details",
        b"QueueStrategy and NotificationChannel are interfaces",
    ):
        assert text in response.data


def test_feedback_page_displays_finding_details_and_recommendations(client):
    create_draft(client)
    weak_design = {
        "classes_text": "Patient and Doctor are classes.",
        "relationships_text": (
            "Patient uses Doctor in a clinic workflow that coordinates care and "
            "records each visit for the learner."
        ),
        "extensibility_text": "",
        "tradeoffs_text": "This is a basic prototype design.",
        "diagram_text": "",
    }
    client.post("/attempts/1/save", data=weak_design)
    client.post("/attempts/1/submit")

    response = client.get("/attempts/1/feedback")

    assert b"Missing queue-token model" in response.data
    assert b"Classes and responsibilities" in response.data
    assert b"Without an object representing a queue token" in response.data
    assert b"Consider adding a QueueToken" in response.data
    assert b"Next improvements" in response.data


def test_failed_feedback_keeps_failure_message_and_retry_action(app, client):
    save_valid_design(client)
    with app.app_context():
        repository = SQLiteAttemptRepository(get_db())
        problems = SQLiteProblemRepository(get_db())
        service = EvaluationService(repository, problems, FailingEvaluator())
        try:
            service.submit_attempt(1, DEMO_LEARNER_ID)
        except Exception:
            pass

    response = client.get("/attempts/1/feedback")

    assert response.status_code == 200
    assert b"Evaluation failed" in response.data
    assert b"We could not evaluate this attempt. Please try again." in response.data
    assert b"Retry Evaluation" in response.data


def test_retry_from_non_failed_attempt_is_rejected(client):
    save_valid_design(client)
    client.post("/attempts/1/submit")

    response = client.post("/attempts/1/retry-evaluation")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/attempts/1/feedback")


class FailingEvaluator:
    name = "test-failing-evaluator"

    def evaluate(self, problem, submission):
        raise RuntimeError("simulated evaluator outage")


def test_evaluator_failure_preserves_submission_and_sets_failed(app, client):
    save_valid_design(client)
    with app.app_context():
        repository = SQLiteAttemptRepository(get_db())
        problems = SQLiteProblemRepository(get_db())
        service = EvaluationService(repository, problems, FailingEvaluator())

        try:
            service.submit_attempt(1, DEMO_LEARNER_ID)
        except Exception as error:
            assert str(error) == GENERIC_EVALUATION_ERROR

        attempt = repository.get_attempt(1, DEMO_LEARNER_ID)
        submission = repository.get_submission(1)
        evaluation = repository.get_evaluation(1)

    assert attempt.status is AttemptStatus.EVALUATION_FAILED
    assert submission.classes_text == valid_design()["classes_text"]
    assert evaluation.error_message == GENERIC_EVALUATION_ERROR


def test_retry_after_failure_succeeds_with_working_evaluator(app, client):
    save_valid_design(client)
    with app.app_context():
        repository = SQLiteAttemptRepository(get_db())
        problems = SQLiteProblemRepository(get_db())
        failing_service = EvaluationService(repository, problems, FailingEvaluator())
        try:
            failing_service.submit_attempt(1, DEMO_LEARNER_ID)
        except Exception:
            pass

        working_service = EvaluationService(repository, problems, PlaceholderEvaluator())
        attempt, evaluation = working_service.retry_evaluation(1, DEMO_LEARNER_ID)
        evaluation_count = get_db().execute(
            "SELECT COUNT(*) FROM evaluations WHERE attempt_id = 1"
        ).fetchone()[0]

    assert attempt.status is AttemptStatus.FEEDBACK_READY
    assert evaluation.overall_score == 60
    assert evaluation_count == 1