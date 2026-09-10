from app.db import get_db


def network_design(strong=True):
    if strong:
        return {
            "classes_text": (
                "SecurityEvent stores source, destination, event type, and timestamp. "
                "Alert represents severity and lifecycle status. AlertManager coordinates "
                "DetectionRule, SeverityPolicy, SecurityAnalyst assignment, and NotificationChannel."
            ),
            "relationships_text": (
                "AlertManager receives a SecurityEvent, applies a DetectionRule, creates an Alert, "
                "assigns it to a SecurityAnalyst, and notifies through NotificationChannel. "
                "An analyst acknowledges and resolves the alert."
            ),
            "extensibility_text": (
                "DetectionRule and SeverityPolicy are interfaces, and NotificationChannel supports "
                "email and dashboard implementations."
            ),
            "tradeoffs_text": (
                "Duplicate events use a fingerprint and time window. Invalid events are rejected. "
                "An unavailable analyst leaves the alert unassigned and notification failure is retried."
            ),
            "diagram_text": "",
        }
    return {
        "classes_text": (
            "SecurityEvent and Alert are classes used to record network incidents and display "
            "alert information to the analyst."
        ),
        "relationships_text": (
            "Events are processed and alerts are created for important network activity."
        ),
        "extensibility_text": "Basic design with simple rules.",
        "tradeoffs_text": "Invalid events are rejected safely.",
        "diagram_text": "",
    }


def create_network_attempt(client):
    response = client.post("/problems/network-intrusion-alert-manager/attempts")
    assert response.status_code == 302
    return response


def test_network_problem_completes_shared_attempt_workflow(client, app):
    create_network_attempt(client)
    save_response = client.post("/attempts/1/save", data=network_design())
    submit_response = client.post("/attempts/1/submit")
    feedback_response = client.get("/attempts/1/feedback")
    history_response = client.get("/history")

    assert save_response.status_code == 302
    assert submit_response.status_code == 302
    assert feedback_response.status_code == 200
    assert b"Network Intrusion Alert Manager" in feedback_response.data
    assert history_response.status_code == 200
    assert b"Network Intrusion Alert Manager" in history_response.data
    with app.app_context():
        evaluation = get_db().execute(
            "SELECT evaluator_name, overall_score FROM evaluations WHERE attempt_id = 1"
        ).fetchone()
    assert evaluation["evaluator_name"] == "rule-based-evaluator"
    assert evaluation["overall_score"] is not None


def test_network_weak_design_receives_domain_feedback_and_scores_lower(client, app):
    create_network_attempt(client)
    client.post("/attempts/1/save", data=network_design(strong=False))
    client.post("/attempts/1/submit")
    weak_score = get_db().execute(
        "SELECT overall_score FROM evaluations WHERE attempt_id = 1"
    ).fetchone()[0]
    weak_feedback = client.get("/attempts/1/feedback")

    client.post("/problems/network-intrusion-alert-manager/attempts")
    client.post("/attempts/2/save", data=network_design(strong=True))
    client.post("/attempts/2/submit")
    strong_score = get_db().execute(
        "SELECT overall_score FROM evaluations WHERE attempt_id = 2"
    ).fetchone()[0]

    assert weak_feedback.status_code == 200
    assert b"Alert-severity policy is not explained" in weak_feedback.data
    assert b"Alert lifecycle is not explained" in weak_feedback.data
    assert b"Missing queue-token model" not in weak_feedback.data
    assert b"Parking-spot model is not explained" not in weak_feedback.data
    assert strong_score > weak_score