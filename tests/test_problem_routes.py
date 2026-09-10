def test_problems_page_lists_seeded_problem(client):
    response = client.get("/problems")

    assert response.status_code == 200
    assert b"Design a Clinic Queue Management System" in response.data
    assert b"Design a Parking Lot Management System" in response.data
    assert b"Network Intrusion Alert Manager" in response.data


def test_network_intrusion_detail_page_shows_design_brief(client):
    response = client.get("/problems/network-intrusion-alert-manager")

    assert response.status_code == 200
    assert b"Network Intrusion Alert Manager" in response.data
    assert b"security events" in response.data.lower()
    assert b"severity" in response.data.lower()


def test_parking_lot_detail_page_shows_design_brief(client):
    response = client.get("/problems/parking-lot-management")

    assert response.status_code == 200
    assert b"Design a Parking Lot Management System" in response.data
    assert b"parking spot" in response.data.lower()
    assert b"parking fee" in response.data.lower()


def test_problem_detail_page_shows_design_brief(client):
    response = client.get("/problems/clinic-queue-management")

    assert response.status_code == 200
    assert b"Functional requirements" in response.data
    assert b"Constraints" in response.data
    assert b"What to submit" in response.data


def test_unknown_problem_returns_not_found(client):
    response = client.get("/problems/not-a-real-problem")

    assert response.status_code == 404