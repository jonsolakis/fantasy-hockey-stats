from uuid import uuid4

from app.main import app
from fastapi.testclient import TestClient


def test_create_and_list_scoring_profile():
    profile_name = f"Goals First {uuid4()}"
    with TestClient(app) as client:
        create_response = client.post(
            "/api/scoring-profiles",
            json={
                "name": profile_name,
                "description": "Reward goals more heavily than assists.",
                "rules": [
                    {"stat_key": "goal", "points": 2.0},
                    {"stat_key": "assist", "points": 1.0},
                ],
            },
        )

        assert create_response.status_code == 201
        assert create_response.json()["name"] == profile_name

        list_response = client.get("/api/scoring-profiles")
        assert list_response.status_code == 200
        assert len(list_response.json()) >= 1
