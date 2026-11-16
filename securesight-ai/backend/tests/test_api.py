import os
os.environ["JWT_SECRET"] = "test-secret-that-is-at-least-32-characters-long"
os.environ["DATABASE_URL"] = "sqlite:///./test_securesight.db"
os.environ["SEED_DEMO_PASSWORD"] = "test-demo-password"
os.environ["OPENAI_API_KEY"] = ""
os.environ["AI_PROVIDER"] = "openai"
from fastapi.testclient import TestClient
from app.database import Base, engine
from app.main import app

def test_health_and_auth_and_assets():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    from app.main import seed_demo
    seed_demo()
    with TestClient(app) as client:
        assert client.get("/api/health").status_code == 200
        assert client.get("/api/assets").status_code == 401
        response = client.post("/api/auth/login", json={"username": "SuPrIyA", "password": "test-demo-password"})
        assert response.status_code == 200
        headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
        assert client.get("/api/organization", headers=headers).status_code == 200
        overview = client.get("/api/overview", headers=headers)
        assert overview.status_code == 200
        assert overview.json()["data_mode"] == "synthetic"
        assert overview.json()["events_analyzed"] == 4
        assert overview.json()["open_incidents"] == 2
        assert client.post("/api/ai/analyze", headers=headers, json={"question": "Summarize this synthetic alert."}).status_code == 503
        unsafe = client.post("/api/ai/analyze", headers=headers, json={"question": "The password=example-secret was exposed."})
        assert unsafe.status_code == 422
        created = client.post("/api/assets", headers=headers, json={"name": "Web", "asset_type": "web", "identifier": "web.example.test"})
        assert created.status_code == 201
        assert len(client.get("/api/assets", headers=headers).json()) == 5
