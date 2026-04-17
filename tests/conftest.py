"""
Configuración y fixtures compartidos para todos los tests.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client() -> TestClient:
    """
    Fixture que proporciona un cliente de test para la aplicación FastAPI.
    """
    # Importamos aquí para evitar problemas de importación circular
    # en la fase inicial del proyecto
    from app.main import create_app

    app = create_app()
    return TestClient(app)
