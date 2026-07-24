from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["app"] == "DocMind Backend API"

def test_list_documents_endpoint():
    response = client.get("/api/docs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_ask_question_empty_validation():
    response = client.post("/api/ask", json={"question": "   ", "category": "All"})
    assert response.status_code == 400
