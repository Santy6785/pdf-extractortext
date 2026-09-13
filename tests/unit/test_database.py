"""
Tests unitarios para el gestor de base de datos (Database).
Verifican el comportamiento de is_connected() con mocks.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


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