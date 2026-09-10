from app.db import get_db


CORE_FIELDS = {
    "classes_text": "",
    "relationships_text": "",
    "extensibility_text": "",
    "tradeoffs_text": "",
    "diagram_text": "",
}


def create_attempt(client):
    response = client.post("/problems/clinic-queue-management/attempts")
    assert response.status_code == 302


def test_incomplete_draft_can_be_saved(client):
    create_attempt(client)

    response = client.post(
        "/attempts/1/save",
        data={**CORE_FIELDS, "classes_text": "One class idea"},
    )

    assert response.status_code == 302


def test_empty_submission_is_rejected_and_stays_draft(client, app):
    create_attempt(client)
    client.post("/attempts/1/save", data=CORE_FIELDS)

    response = client.post("/attempts/1/submit")

    assert response.status_code == 400
    assert b"Describe at least one class or responsibility" in response.data
    with app.app_context():
        status = get_db().execute(
            "SELECT status FROM attempts WHERE id = 1"
        ).fetchone()["status"]
    assert status == "DRAFT"


def test_whitespace_only_core_fields_are_rejected(client, app):
    create_attempt(client)
    client.post(
        "/attempts/1/save",
        data={**CORE_FIELDS, "classes_text": "   ", "relationships_text": "\n\t"},
    )

    response = client.post("/attempts/1/submit")

    assert response.status_code == 400
    assert b"Describe at least one class or responsibility" in response.data
    assert b"Describe the relationships and main workflow" in response.data
    with app.app_context():
        status = get_db().execute(
            "SELECT status FROM attempts WHERE id = 1"
        ).fetchone()["status"]
    assert status == "DRAFT"


def test_validation_failure_preserves_saved_draft_content(client, app):
    create_attempt(client)
    saved = {
        **CORE_FIELDS,
        "classes_text": "Saved class responsibility",
        "relationships_text": "Saved workflow relationship",
    }
    client.post("/attempts/1/save", data=saved)

    response = client.post("/attempts/1/submit")

    assert response.status_code == 400
    assert b"Saved class responsibility" in response.data
    assert b"Saved workflow relationship" in response.data
    with app.app_context():
        row = get_db().execute(
            "SELECT classes_text, relationships_text, status FROM attempts "
            "JOIN submissions ON submissions.attempt_id = attempts.id "
            "WHERE attempts.id = 1"
        ).fetchone()
    assert row["classes_text"] == saved["classes_text"]
    assert row["relationships_text"] == saved["relationships_text"]
    assert row["status"] == "DRAFT"