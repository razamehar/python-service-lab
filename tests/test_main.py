
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to the AWS CI/CD Demo API"
    }


def test_health_check_response_content_type():
    response = client.get("/health")

    assert response.headers["content-type"] == "application/json"


def test_unknown_endpoint_returns_404():
    response = client.get("/unknown")

    assert response.status_code == 404


def test_request_logging(caplog):
    with caplog.at_level("INFO", logger="app"):
        response = client.get("/health")

    assert response.status_code == 200
    assert "Request completed" in caplog.text
    assert "method=GET" in caplog.text
    assert "path=/health" in caplog.text
    assert "status_code=200" in caplog.text
