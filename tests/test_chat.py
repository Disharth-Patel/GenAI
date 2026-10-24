import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def student_auth_headers(client):
    """Register and log in a test student user."""
    # Try logging in first
    login_resp = client.post("/api/auth/login", json={
        "username_or_email": "student",
        "password": "Student@123"
    })
    if login_resp.status_code == 200:
        token = login_resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    # Otherwise register
    reg_resp = client.post("/api/auth/register", json={
        "username": "test_student",
        "email": "test_student@example.com",
        "password": "Password@123"
    })
    token = reg_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def second_student_headers(client):
    """Register a second student user for privacy boundary tests."""
    login_resp = client.post("/api/auth/login", json={
        "username_or_email": "student_two",
        "password": "Password@123"
    })
    if login_resp.status_code == 200:
        token = login_resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    reg_resp = client.post("/api/auth/register", json={
        "username": "student_two",
        "email": "student_two@example.com",
        "password": "Password@123"
    })
    token = reg_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_empty_message_rejected(client):
    """Reject empty messages with 400 or 422."""
    res = client.post("/api/chat", json={"message": "   "})
    assert res.status_code == 400


def test_normal_chat_query_returns_answer_and_sources(client):
    """Verify chat endpoint returns answer, conversation_id, and sources."""
    res = client.post("/api/chat", json={
        "message": "What is the Post Matric Scholarship for OBC students in Maharashtra?",
        "language": "en"
    })
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert len(data["answer"]) > 10
    assert "conversation_id" in data
    assert "sources" in data
    assert isinstance(data["sources"], list)


def test_multilingual_marathi_chat(client):
    """Verify Marathi question receives grounded response."""
    res = client.post("/api/chat", json={
        "message": "ओबीसी विद्यार्थ्यांसाठी कोणती शिष्यवृत्ती योजना आहे?",
        "language": "auto"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["language"] in ["mr", "hi"]
    assert len(data["sources"]) > 0


def test_user_cannot_access_other_users_conversation(client, student_auth_headers, second_student_headers):
    """User A cannot read User B's conversation history."""
    # User 1 creates a conversation
    chat_resp = client.post(
        "/api/chat",
        headers=student_auth_headers,
        json={"message": "Hello from student one!"}
    )
    assert chat_resp.status_code == 200
    conv_id = chat_resp.json()["conversation_id"]

    # User 1 can view it
    conv1 = client.get(f"/api/conversations/{conv_id}", headers=student_auth_headers)
    assert conv1.status_code == 200

    # User 2 tries to view it -> 403 Forbidden
    conv2 = client.get(f"/api/conversations/{conv_id}", headers=second_student_headers)
    assert conv2.status_code in [403, 404]


def test_speech_synthesize_endpoint(client):
    """Test speech synthesis configuration route."""
    res = client.post("/api/speech/synthesize", json={
        "text": "Hello, welcome to Maharashtra OBC education portal.",
        "language": "en"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert "voice" in data
    assert data["voice"]["target_locale"] == "en-IN"
