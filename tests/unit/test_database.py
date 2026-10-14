"""
Tests unitarios para el gestor de base de datos (Database).
Verifican el comportamiento de connect(), disconnect() e is_connected() con mocks.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture(autouse=True)
def reset_database_state():
    """Resetea el estado del singleton Database antes y después de cada test."""
    from app.infrastructure.persistence.database import Database

    def _reset():
        Database._client = None
        Database._db = None
        if Database._instance is not None:
            Database._instance._client = None
            Database._instance._db = None

    _reset()
    yield
    _reset()


class TestDatabaseConnect:
    """Tests para el método connect() del gestor de base de datos."""

    @pytest.mark.asyncio
    async def test_connect_initializes_client_with_configured_uri(self):
        """Test que connect inicializa AsyncIOMotorClient con la URI de configuración."""
        from app.infrastructure.persistence.database import Database

        mock_client = MagicMock()

        with patch(
            "app.infrastructure.persistence.database.AsyncIOMotorClient",
            return_value=mock_client,
        ) as mock_client_cls:
            db = Database()
            await db.connect()

            mock_client_cls.assert_called_once_with("mongodb://localhost:27017")
            assert db._client is mock_client
            assert db._db is mock_client["pdf_extractor"]

    @pytest.mark.asyncio
    async def test_connect_does_not_recreate_client_if_already_connected(self):
        """Test que connect no crea un nuevo cliente si ya existe uno."""
        from app.infrastructure.persistence.database import Database

        db = Database()
        existing_client = MagicMock()
        db._client = existing_client

        with patch(
            "app.infrastructure.persistence.database.AsyncIOMotorClient"
        ) as mock_client_cls:
            await db.connect()

            mock_client_cls.assert_not_called()
            assert db._client is existing_client

    @pytest.mark.asyncio
    async def test_connect_propagates_exception_when_client_init_fails(self):
        """Test que connect propaga la excepción si falla la inicialización del cliente."""
        from app.infrastructure.persistence.database import Database

        with patch(
            "app.infrastructure.persistence.database.AsyncIOMotorClient",
            side_effect=Exception("Invalid URI"),
        ):
            db = Database()
            with pytest.raises(Exception, match="Invalid URI"):
                await db.connect()

            assert db._client is None
            assert db._db is None


class TestDatabaseDisconnect:
    """Tests para el método disconnect() del gestor de base de datos."""

    @pytest.mark.asyncio
    async def test_disconnect_closes_client_and_resets_state(self):
        """Test que disconnect cierra el cliente y resetea el estado a None."""
        from app.infrastructure.persistence.database import Database

        db = Database()
        mock_client = MagicMock()
        db._client = mock_client
        db._db = MagicMock()

        await db.disconnect()

        mock_client.close.assert_called_once()
        assert db._client is None
        assert db._db is None

    @pytest.mark.asyncio
    async def test_disconnect_does_nothing_when_not_connected(self):
        """Test que disconnect no falla ni hace nada si no hay cliente."""
        from app.infrastructure.persistence.database import Database

        db = Database()
        db._client = None
        db._db = None

        await db.disconnect()

        assert db._client is None
        assert db._db is None


class TestDatabaseIsConnected:
    """Tests para el método is_connected() del gestor de base de datos."""

    @pytest.mark.asyncio
    async def test_is_connected_returns_true_when_ping_succeeds(self):
        """Test que is_connected retorna True cuando el ping a MongoDB es exitoso."""
        from app.infrastructure.persistence.database import Database

        db = Database()
        db._client = MagicMock()
        db._db = MagicMock()

        mock_admin = MagicMock()
        mock_admin.command = AsyncMock(return_value={"ok": 1})
        db._client.admin = mock_admin

        result = await db.is_connected()

        assert result is True
        mock_admin.command.assert_awaited_once_with("ping")

    @pytest.mark.asyncio
    async def test_is_connected_returns_false_when_client_is_none(self):
        """Test que is_connected retorna False cuando _client es None."""
        from app.infrastructure.persistence.database import Database

        db = Database()
        db._client = None
        db._db = None

        result = await db.is_connected()

        assert result is False

    @pytest.mark.asyncio
    async def test_is_connected_returns_false_when_db_is_none(self):
        """Test que is_connected retorna False cuando _db es None."""
        from app.infrastructure.persistence.database import Database

        db = Database()
        db._client = MagicMock()
        db._db = None

        result = await db.is_connected()

        assert result is False

    @pytest.mark.asyncio
    async def test_is_connected_returns_false_when_ping_fails(self):
        """Test que is_connected retorna False cuando el ping falla con excepción."""
        from app.infrastructure.persistence.database import Database

        db = Database()
        db._client = MagicMock()
        db._db = MagicMock()

        mock_admin = MagicMock()
        mock_admin.command = AsyncMock(side_effect=Exception("Connection failed"))
        db._client.admin = mock_admin

        result = await db.is_connected()

        assert result is False
        mock_admin.command.assert_awaited_once_with("ping")


class TestHealthCheckEndpoint:
    """Tests para el endpoint de health check."""

    @pytest.mark.asyncio
    async def test_health_check_returns_healthy_when_db_connected(self, client):
        """Test que health check retorna healthy cuando la BD está conectada."""
        from app.infrastructure.persistence.database import database

        mock_admin = MagicMock()
        mock_admin.command = AsyncMock(return_value={"ok": 1})
        database._client = MagicMock()
        database._db = MagicMock()
        database._client.admin = mock_admin

        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"

    @pytest.mark.asyncio
    async def test_health_check_returns_unhealthy_when_db_disconnected(self, client):
        """Test que health check retorna unhealthy cuando la BD no está conectada."""
        from app.infrastructure.persistence.database import database

        database._client = None
        database._db = None

        response = client.get("/api/v1/health")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database"] == "disconnected"

    @pytest.mark.asyncio
    async def test_health_check_returns_unhealthy_when_ping_fails(self, client):
        """Test que health check retorna unhealthy cuando el ping falla."""
        from app.infrastructure.persistence.database import database

        mock_admin = MagicMock()
        mock_admin.command = AsyncMock(side_effect=Exception("Connection failed"))
        database._client = MagicMock()
        database._db = MagicMock()
        database._client.admin = mock_admin

        response = client.get("/api/v1/health")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database"] == "disconnected"