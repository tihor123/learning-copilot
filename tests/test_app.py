from fastapi.testclient import TestClient
import pytest

from src import app as app_module

client = TestClient(app_module.app)

# copy of the original activities so we can restore state between tests
original_activities = {k: {**v, "participants": list(v["participants"])}
                       for k, v in app_module.activities.items()}

@pytest.fixture(autouse=True)
def reset_activities():
    # clear and repopulate the in-memory activities dict before each test
    app_module.activities.clear()
    for name, details in original_activities.items():
        app_module.activities[name] = {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": list(details["participants"]),
        }
    yield


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # should contain one of the known activities
    assert "Chess Club" in data

def test_signup_success():
    resp = client.post("/activities/Chess%20Club/signup?email=test@school.edu")
    assert resp.status_code == 200
    assert "Signed up" in resp.json().get("message", "")
    # verify member added
    assert "test@school.edu" in app_module.activities["Chess Club"]["participants"]

def test_signup_duplicate():
    email = "michael@mergington.edu"
    # first signup succeed
    resp1 = client.post(f"/activities/Chess%20Club/signup?email={email}")
    assert resp1.status_code == 400 or resp1.status_code == 200
    # second should return error (400)
    resp2 = client.post(f"/activities/Chess%20Club/signup?email={email}")
    assert resp2.status_code == 400
    assert "already signed up" in resp2.json().get("detail", "")

def test_signup_nonexistent():
    resp = client.post("/activities/NoSuch/signup?email=x@x.com")
    assert resp.status_code == 404


def test_unregister_success():
    email = "michael@mergington.edu"
    resp = client.delete(f"/activities/Chess%20Club/signup?email={email}")
    assert resp.status_code == 200
    assert "Unregistered" in resp.json().get("message", "")
    assert email not in app_module.activities["Chess Club"]["participants"]

def test_unregister_nonexistent():
    resp = client.delete("/activities/Chess%20Club/signup?email=not@there.com")
    assert resp.status_code == 404
