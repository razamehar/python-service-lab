
from contextlib import asynccontextmanager
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app import main as main_module
from app.services import github_mcp as github_mcp_module

app = main_module.app
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


def setup_mcp_mocks(monkeypatch, mock_result):
    """Replace external MCP dependencies with local test doubles."""

    class FakeAsyncClient:
        def __init__(self, **kwargs):
            self.headers = kwargs.get("headers")

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_value, traceback):
            pass

    @asynccontextmanager
    async def fake_streamable_http_client(*args, **kwargs):
        yield object(), object()

    class FakeClientSession:
        last_tool_name = None
        last_arguments = None

        def __init__(self, read_stream, write_stream):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_value, traceback):
            pass

        async def initialize(self):
            pass

        async def call_tool(self, name, arguments):
            FakeClientSession.last_tool_name = name
            FakeClientSession.last_arguments = arguments
            return mock_result

    monkeypatch.setattr(
    github_mcp_module.httpx2,
    "AsyncClient",
    FakeAsyncClient,
)

    monkeypatch.setattr(
        github_mcp_module,
        "streamable_http_client",
        fake_streamable_http_client,
    )

    monkeypatch.setattr(
        github_mcp_module,
        "ClientSession",
        FakeClientSession,
    )

    return FakeClientSession


def test_github_file_retrieval_success(monkeypatch):
    monkeypatch.setenv("GITHUB_MCP_TOKEN", "test-token")

    mock_result = SimpleNamespace(
        is_error=False,
        content=[
            SimpleNamespace(text="print('Hello from GitHub')")
        ],
    )

    fake_session = setup_mcp_mocks(monkeypatch, mock_result)

    response = client.get(
        "/github/file",
        params={"path": "app/main.py"},
    )

    assert response.status_code == 200
    assert response.json() == {
    "repository": "razamehar/python-service-lab",
    "path": "app/main.py",
    "content": ["print('Hello from GitHub')"],
}

    assert fake_session.last_tool_name == "get_file_contents"
    assert fake_session.last_arguments == {
        "owner": "razamehar",
        "repo": "python-service-lab",
        "path": "app/main.py",
    }


def test_github_file_mcp_tool_error(monkeypatch):
    monkeypatch.setenv("GITHUB_MCP_TOKEN", "test-token")

    mock_result = SimpleNamespace(
        is_error=True,
        content=[
            SimpleNamespace(text="File not found")
        ],
    )

    setup_mcp_mocks(monkeypatch, mock_result)

    response = client.get(
        "/github/file",
        params={"path": "missing.py"},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == ["File not found"]


def test_github_file_missing_token(monkeypatch):
    monkeypatch.delenv("GITHUB_MCP_TOKEN", raising=False)

    response = client.get(
        "/github/file",
        params={"path": "app/main.py"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "GitHub MCP token is not configured."
    )
