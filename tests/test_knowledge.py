import io
import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def admin_auth_headers(client):
    """Log in as default seeded administrator."""
    res = client.post("/api/auth/login", json={
        "username_or_email": "admin",
        "password": "Admin@123"
    })
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def student_auth_headers(client):
    """Register or log in a regular student user."""
    login_res = client.post("/api/auth/login", json={
        "username_or_email": "student",
        "password": "Student@123"
    })
    if login_res.status_code == 200:
        token = login_res.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    reg_res = client.post("/api/auth/register", json={
        "username": "student_k_test",
        "email": "student_k_test@example.com",
        "password": "Student@123"
    })
    token = reg_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_student_cannot_access_admin_knowledge_routes(client, student_auth_headers):
    """Phase G & H: Students are forbidden from admin knowledge endpoints."""
    res = client.get("/api/knowledge", headers=student_auth_headers)
    assert res.status_code == 403

    create_res = client.post("/api/knowledge", headers=student_auth_headers, json={
        "title": "Unauthorized Entry",
        "content": "This should be blocked."
    })
    assert create_res.status_code == 403


def test_admin_can_list_knowledge(client, admin_auth_headers):
    """Admin can query knowledge entries."""
    res = client.get("/api/knowledge?limit=5", headers=admin_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert data["total"] > 0
    assert len(data["items"]) <= 5


def test_knowledge_crud_and_automatic_synchronization(client, admin_auth_headers):
    """
    Phase H: Adding an entry updates the knowledge base and makes it
    retrievable in subsequent chat questions without restarting.
    """
    unique_keyword = "ZyxOBCSpecialScheme999"

    # 1. Create new knowledge entry
    create_res = client.post("/api/knowledge", headers=admin_auth_headers, json={
        "title": f"Special Fellowship {unique_keyword}",
        "content": f"The {unique_keyword} provides 50000 rupees stipend for OBC robotics researchers in Maharashtra.",
        "record_type": "scheme",
        "category": "higher_education",
        "official_source": "https://mahadbt.maharashtra.gov.in/special",
        "keywords": f"{unique_keyword}; robotics; stipend",
    })
    assert create_res.status_code == 201
    entry_id = create_res.json()["id"]

    # 2. Query chat with this unique keyword -> Verify it is retrieved!
    chat_res = client.post("/api/chat", json={
        "message": f"How much stipend does {unique_keyword} offer?",
        "language": "en"
    })
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert unique_keyword in chat_data["answer"] or any(unique_keyword in s["title"] for s in chat_data["sources"])

    # 3. Update entry
    update_res = client.put(f"/api/knowledge/{entry_id}", headers=admin_auth_headers, json={
        "title": f"Updated Fellowship {unique_keyword}",
        "content": f"The updated {unique_keyword} now provides 75000 rupees stipend."
    })
    assert update_res.status_code == 200

    # 4. Delete entry
    del_res = client.delete(f"/api/knowledge/{entry_id}", headers=admin_auth_headers)
    assert del_res.status_code == 204


def test_unsupported_file_upload_rejected(client, admin_auth_headers):
    """Upload endpoint must reject invalid file types."""
    dummy_file = io.BytesIO(b"malicious script content")
    res = client.post(
        "/api/knowledge/upload",
        headers=admin_auth_headers,
        files={"file": ("exploit.exe", dummy_file, "application/octet-stream")}
    )
    assert res.status_code == 400
    assert "Unsupported file format" in res.json()["detail"]


def test_txt_document_upload_and_indexing(client, admin_auth_headers):
    """Admin can upload TXT document and it is parsed and indexed."""
    txt_content = b"Maharashtra OBC Hostel Scheme Guidelines 2026. Free lodging and food allowance provided to eligible students."
    res = client.post(
        "/api/knowledge/upload",
        headers=admin_auth_headers,
        files={"file": ("hostel_guidelines_2026.txt", io.BytesIO(txt_content), "text/plain")},
        data={"title": "Hostel Guidelines 2026", "category": "hostel_support"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["chunks_indexed"] >= 1
