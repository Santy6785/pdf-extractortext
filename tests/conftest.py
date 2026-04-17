import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client() -> TestClient:

    from app.main import create_app

    app = create_app()
    return TestClient(app)
