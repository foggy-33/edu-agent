from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze() -> None:
    response = client.post(
        "/api/analyze",
        json={
            "user_id": "demo_user_001",
            "course": "数据库系统",
            "message": "我是计算机专业大二学生，对函数依赖、候选码和范式判断不太会，希望通过例题准备考试。",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "profile" in data
    assert "函数依赖" in data["profile"]["weak_points"]


def test_generate() -> None:
    response = client.post(
        "/api/generate",
        json={
            "user_id": "demo_user_001",
            "course": "数据库系统",
            "message": "我是计算机专业大二学生，正在学习数据库系统。我对函数依赖、候选码和范式判断不太会，希望通过例题和步骤化讲解准备考试。",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["resources"]["mindmap"].startswith("mindmap")
    assert len(data["resources"]["quiz"]) >= 5
    assert "CREATE TABLE" in data["resources"]["practice_case"]
