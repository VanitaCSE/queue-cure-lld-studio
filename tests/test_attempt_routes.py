from app.db import get_db


def create_attempt(client):
    response = client.post(
        "/problems/clinic-queue-management/attempts", follow_redirects=False
    )
    assert response.status_code == 302
    return response


def test_create_attempt_redirects_to_editor(client):
    response = create_attempt(client)

    assert "/attempts/1/edit" in response.headers["Location"]
    editor = client.get(response.headers["Location"])
    assert editor.status_code == 200
    assert b"Your Design Attempt" in editor.data


def test_new_attempt_is_draft_with_blank_submission(client, app):
    create_attempt(client)

    with app.app_context():
        attempt = get_db().execute("SELECT * FROM attempts").fetchone()
        submission = get_db().execute("SELECT * FROM submissions").fetchone()

    assert attempt["status"] == "DRAFT"
    assert submission["attempt_id"] == attempt["id"]
    assert all(submission[field] == "" for field in (
        "classes_text",
        "relationships_text",
        "extensibility_text",
        "tradeoffs_text",
        "diagram_text",
    ))


def test_save_draft_persists_all_fields(client, app):
    create_attempt(client)
    values = {
        "classes_text": "Patient and QueueToken",
        "relationships_text": "QueueService creates QueueToken",
        "extensibility_text": "QueueStrategy interface",
        "tradeoffs_text": "Cancellation is a state transition",
        "diagram_text": "classDiagram",
    }

    response = client.post("/attempts/1/save", data=values)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/attempts/1/edit")
    with app.app_context():
        submission = get_db().execute("SELECT * FROM submissions").fetchone()
    for field, value in values.items():
        assert submission[field] == value


def test_empty_fields_are_allowed(client):
    create_attempt(client)

    response = client.post(
        "/attempts/1/save",
        data={field: "" for field in (
            "classes_text",
            "relationships_text",
            "extensibility_text",
            "tradeoffs_text",
            "diagram_text",
        )},
    )

    assert response.status_code == 302


def test_long_field_is_rejected_without_overwriting_saved_data(client, app):
    create_attempt(client)
    client.post("/attempts/1/save", data={"classes_text": "saved design"})

    response = client.post(
        "/attempts/1/save", data={"classes_text": "x" * 10001}
    )

    assert response.status_code == 400
    assert b"10,000 characters or fewer" in response.data
    with app.app_context():
        saved_value = get_db().execute(
            "SELECT classes_text FROM submissions WHERE attempt_id = 1"
        ).fetchone()["classes_text"]
    assert saved_value == "saved design"


def test_history_displays_learner_attempts(client):
    create_attempt(client)

    response = client.get("/history")

    assert response.status_code == 200
    assert b"My Design Attempts" in response.data
    assert b"Design a Clinic Queue Management System" in response.data
    assert b"Continue Draft" in response.data


def test_unknown_problem_cannot_create_attempt(client):
    response = client.post("/problems/not-a-real-problem/attempts")

    assert response.status_code == 404


def test_unknown_attempt_returns_not_found(client):
    assert client.get("/attempts/999/edit").status_code == 404
    assert client.post("/attempts/999/save", data={}).status_code == 404