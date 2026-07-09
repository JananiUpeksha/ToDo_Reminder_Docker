from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base
from app.main import get_db

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    mock = MagicMock()
    mock.get.return_value = None
    monkeypatch.setattr("app.main.redis_client", mock)


client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "To-Do Reminder API is running"}


def test_create_todo():
    payload = {
        "title": "Buy groceries",
        "description": "Milk and eggs",
        "due_at": "2026-12-01T10:00:00"
    }
    response = client.post("/todos", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Buy groceries"
    assert data["is_completed"] == False
    assert data["reminder_sent"] == False
    assert "id" in data


def test_list_todos_empty():
    response = client.get("/todos")
    assert response.status_code == 200
    assert response.json() == []


def test_list_todos_after_create():
    client.post("/todos", json={"title": "Task 1", "due_at": "2026-12-01T10:00:00"})
    client.post("/todos", json={"title": "Task 2", "due_at": "2026-12-02T10:00:00"})
    response = client.get("/todos")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_todo_by_id():
    create_response = client.post(
        "/todos",
        json={"title": "Specific task", "due_at": "2026-12-01T10:00:00"}
    )
    todo_id = create_response.json()["id"]
    response = client.get(f"/todos/{todo_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Specific task"


def test_get_todo_not_found():
    response = client.get("/todos/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Todo not found"


def test_update_todo():
    create_response = client.post(
        "/todos",
        json={"title": "Old title", "due_at": "2026-12-01T10:00:00"}
    )
    todo_id = create_response.json()["id"]
    response = client.put(f"/todos/{todo_id}", json={"title": "New title"})
    assert response.status_code == 200
    assert response.json()["title"] == "New title"


def test_mark_complete():
    create_response = client.post(
        "/todos",
        json={"title": "Finish project", "due_at": "2026-12-01T10:00:00"}
    )
    todo_id = create_response.json()["id"]
    response = client.patch(f"/todos/{todo_id}/complete")
    assert response.status_code == 200
    assert response.json()["is_completed"] == True


def test_delete_todo():
    create_response = client.post(
        "/todos",
        json={"title": "To be deleted", "due_at": "2026-12-01T10:00:00"}
    )
    todo_id = create_response.json()["id"]
    delete_response = client.delete(f"/todos/{todo_id}")
    assert delete_response.status_code == 204
    get_response = client.get(f"/todos/{todo_id}")
    assert get_response.status_code == 404
