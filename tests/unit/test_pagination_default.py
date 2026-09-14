"""
Tests para verificar que default_page_size de la configuración es la fuente
de verdad del tamaño de página por defecto en la paginación del endpoint
GET /api/v1/documents/.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import router
from app.api.dependencies import get_document_service
from app.application.config_service import get_config_service


def _make_client(default_page_size: int) -> tuple[TestClient, MagicMock]:
    """
    Construye un TestClient con el servicio de documentos y el servicio de
    configuración mockeados.

    Args:
        default_page_size: Valor que retornará config.get_default_page_size()

    Returns:
        Tupla (TestClient, servicio mockeado)
    """
    mock_service = MagicMock()
    mock_service.get_all = AsyncMock(return_value=[])

    mock_config = MagicMock()
    mock_config.get_default_page_size.return_value = default_page_size

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_document_service] = lambda: mock_service
    app.dependency_overrides[get_config_service] = lambda: mock_config

    return TestClient(app), mock_service


def test_list_documents_without_limit_uses_default_page_size():
    """Sin limit explícito, se usa default_page_size de la configuración."""
    client, mock_service = _make_client(default_page_size=20)

    response = client.get("/api/v1/documents/")

    assert response.status_code == 200
    mock_service.get_all.assert_called_once_with(skip=0, limit=20)


def test_list_documents_uses_changed_default_page_size():
    """Si default_page_size cambia, se usa el nuevo valor sin tocar código."""
    client, mock_service = _make_client(default_page_size=7)

    response = client.get("/api/v1/documents/")

    assert response.status_code == 200
    mock_service.get_all.assert_called_once_with(skip=0, limit=7)


def test_list_documents_explicit_limit_takes_precedence():
    """Un limit explícito del cliente tiene prioridad sobre default_page_size."""
    client, mock_service = _make_client(default_page_size=20)

    response = client.get("/api/v1/documents/?skip=3&limit=5")

    assert response.status_code == 200
    mock_service.get_all.assert_called_once_with(skip=3, limit=5)


def test_list_documents_limit_validation_unchanged():
    """Los límites de validación (ge=1, le=100) se mantienen."""
    client, mock_service = _make_client(default_page_size=20)

    assert client.get("/api/v1/documents/?limit=0").status_code == 422
    assert client.get("/api/v1/documents/?limit=101").status_code == 422
    mock_service.get_all.assert_not_called()


def test_config_service_exposes_default_page_size():
    """El ConfigService concreto expone default_page_size de Settings."""
    config = get_config_service()

    from app.config.settings import get_settings
    assert config.get_default_page_size() == get_settings().default_page_size
