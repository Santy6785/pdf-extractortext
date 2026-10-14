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

# Campos del esquema del Document (fuente única de verdad para tests)
# El contrato exhaustivo del modelo se verifica en tests/unit/test_document.py
DOCUMENT_REQUIRED_FIELDS = {"id", "checksum", "extracted_text", "created_at"}


@pytest.fixture(scope="session")
def client():
    """
    Fixture que proporciona un TestClient de FastAPI.
    Mockea la conexión a MongoDB para pruebas.
    """
    from app.main import create_app
    from app.infrastructure.persistence.database import database

  # Mockear la colección con métodos asíncronos
    mock_insert_result = MagicMock()
    mock_insert_result.inserted_id = "65f1a2b3c4d5e6f7a8b9c0d1"

    mock_coll = MagicMock()
    mock_coll.insert_one = AsyncMock(return_value=mock_insert_result)
    mock_coll.find_one = AsyncMock(return_value=None)
    mock_coll.find = MagicMock()
    mock_coll.delete_one = AsyncMock()
    mock_coll.count_documents = AsyncMock(return_value=0)

    # Mockear la base de datos para que devuelva la colección asíncrona
    mock_db = MagicMock()
    mock_db.__getitem__.return_value = mock_coll
    mock_db.get_collection.return_value = mock_coll

    database._client = MagicMock()
    database._db = mock_db

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



