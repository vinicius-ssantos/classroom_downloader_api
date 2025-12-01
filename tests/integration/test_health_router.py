"""
Integration tests for health check endpoints
"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_endpoint_returns_ok(client: AsyncClient):
    """Test basic health check endpoint"""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_db_endpoint_checks_database(client: AsyncClient):
    """Test database health check endpoint"""
    response = await client.get("/health/db")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_root_endpoint_returns_api_info(client: AsyncClient):
    """Test root endpoint returns API information"""
    response = await client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "docs" in data
    assert data["docs"] == "/docs"
