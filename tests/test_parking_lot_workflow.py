from app.db import get_db


def parking_design(strong=True):
    if strong:
        return {
            "classes_text": (
                "Vehicle stores type and registration. ParkingSpot stores spot type, "
                "availability, and compatibility. ParkingLot owns spots. "
                "ParkingTicket stores entry information. ParkingService coordinates "
                "allocation and release."
            ),
            "relationships_text": (
                "ParkingService matches a Vehicle to a suitable ParkingSpot, creates "
                "a ParkingTicket on entry, releases the spot on exit, and uses "
                "PricingStrategy to calculate the fee from duration."
            ),
            "extensibility_text": (
                "PricingStrategy supports hourly and vehicle-specific rates. "
                "Vehicle and spot compatibility can support new types."
            ),
            "tradeoffs_text": (
                "If no suitable spot is available, entry is rejected. One active "
                "ticket occupies one spot. Pricing remains separate from allocation."
            ),
            "diagram_text": "",
        }
    return {
        "classes_text": "Vehicle and ParkingLot are classes.",
        "relationships_text": (
            "ParkingService manages vehicles in a parking workflow and records entry "
            "information for the learner."
        ),
        "extensibility_text": "",
        "tradeoffs_text": "Basic parking design.",
        "diagram_text": "",
    }


def create_parking_attempt(client):
    response = client.post("/problems/parking-lot-management/attempts")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/attempts/1/edit")


def test_parking_attempt_can_be_created_saved_and_evaluated(client, app):
    create_parking_attempt(client)
    values = parking_design()

    save_response = client.post("/attempts/1/save", data=values)
    submit_response = client.post("/attempts/1/submit")
    feedback_response = client.get("/attempts/1/feedback")
    history_response = client.get("/history")

    assert save_response.status_code == 302
    assert submit_response.status_code == 302
    assert feedback_response.status_code == 200
    assert b"Design a Parking Lot Management System" in feedback_response.data
    assert history_response.status_code == 200
    assert b"Design a Parking Lot Management System" in history_response.data
    with app.app_context():
        attempt = get_db().execute(
            "SELECT status FROM attempts WHERE id = 1"
        ).fetchone()
        evaluation = get_db().execute(
            "SELECT evaluator_name, overall_score FROM evaluations WHERE attempt_id = 1"
        ).fetchone()
    assert attempt["status"] == "FEEDBACK_READY"
    assert evaluation["evaluator_name"] == "rule-based-evaluator"
    assert evaluation["overall_score"] is not None


def test_parking_weak_submission_receives_relevant_feedback_and_scores_lower(
    client, app
):
    create_parking_attempt(client)
    client.post("/attempts/1/save", data=parking_design(strong=False))
    client.post("/attempts/1/submit")
    weak_score = get_db().execute(
        "SELECT overall_score FROM evaluations WHERE attempt_id = 1"
    ).fetchone()[0]
    weak_feedback = client.get("/attempts/1/feedback")

    client.post("/problems/parking-lot-management/attempts")
    client.post("/attempts/2/save", data=parking_design(strong=True))
    client.post("/attempts/2/submit")
    strong_score = get_db().execute(
        "SELECT overall_score FROM evaluations WHERE attempt_id = 2"
    ).fetchone()[0]

    assert weak_feedback.status_code == 200
    assert b"Parking-spot model is not explained" in weak_feedback.data
    assert strong_score > weak_score