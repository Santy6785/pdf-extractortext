"""
Configuración de pytest y fixtures compartidos.
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

# Agregar el directorio raíz al path para importar app
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def client():
    """
    Fixture que proporciona un TestClient de FastAPI.
    Mockea la conexión a MongoDB para pruebas.
    """
    from app.main import create_app
    from app.infrastructure.persistence.database import database
    
    # Mockear la conexión a base de datos
    database._client = MagicMock()
    database._db = MagicMock()
    
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_mongo_collection():
    """Fixture que proporciona un mock de colección MongoDB."""
    collection = MagicMock()
    collection.insert_one = AsyncMock()
    collection.find_one = AsyncMock()
    collection.find = MagicMock()
    collection.delete_one = AsyncMock()
    return collection


@pytest.fixture
def sample_pdf_bytes():
    """Fixture que proporciona bytes de PDF de prueba mínimos."""
    # Este es un PDF mínimo válido para pruebas
    # En tests reales, usarías un archivo PDF real o un mock más completo
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids []\n/Count 0\n>>\nendobj\nxref\n0 3\n0000000000 65535 f \n0000000009 00000 n \n0000000052 00000 n \ntrailer\n<<\n/Size 3\n/Root 1 0 R\n>>\nstartxref\n104\n%%EOF"


@pytest.fixture
def mock_pdf_processing_result():
    """Fixture que proporciona un resultado de procesamiento mock."""
    from app.services.pdf_service import PdfProcessingResult
    return PdfProcessingResult(
        nombre_archivo="test.pdf",
        checksum="test-checksum-1234567890abcdef",
        dimensiones_paginas=[{"ancho": 595.0, "alto": 842.0}],
        texto_extraido="Texto de prueba extraído del PDF"
    )
