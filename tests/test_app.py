import importlib.util
import pathlib

from fastapi.testclient import TestClient


def load_app_module():
    # Load a fresh copy of the app module to avoid cross-test state
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    app_path = repo_root / "src" / "app.py"
    spec = importlib.util.spec_from_file_location("app_module", str(app_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_get_activities():
    mod = load_app_module()
    client = TestClient(mod.app)

    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # Ensure a known activity exists
    assert "Chess Club" in data


def test_signup_and_delete_participant_flow():
    mod = load_app_module()
    client = TestClient(mod.app)

    activity = "Chess Club"
    email = "tester@example.com"

    # Ensure the participant is not already present
    before = client.get("/activities").json()
    assert email not in before[activity]["participants"]

    # Sign up
    signup_resp = client.post(f"/activities/{activity}/signup?email={email}")
    assert signup_resp.status_code == 200
    assert "Signed up" in signup_resp.json().get("message", "")

    # Confirm participant now present
    after = client.get("/activities").json()
    assert email in after[activity]["participants"]

    # Sign up same email again -> should fail
    dup = client.post(f"/activities/{activity}/signup?email={email}")
    assert dup.status_code == 400

    # Remove participant
    del_resp = client.delete(f"/activities/{activity}/participants?email={email}")
    assert del_resp.status_code == 200
    assert "Removed" in del_resp.json().get("message", "")

    # Confirm participant removed
    final = client.get("/activities").json()
    assert email not in final[activity]["participants"]


def test_delete_nonexistent_participant():
    mod = load_app_module()
    client = TestClient(mod.app)

    activity = "Chess Club"
    email = "nonexistent@example.com"

    resp = client.delete(f"/activities/{activity}/participants?email={email}")
    assert resp.status_code == 404
