import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Agregar el directorio raíz al path para importar APP
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def client() -> TestClient:
    from APP.main import create_app

    app = create_app()
    return TestClient(app)
