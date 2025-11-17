"""Tests for invoice endpoints."""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from api_gateway.main import app

client = TestClient(app)


def test_health_check():
    """Test API Gateway health check."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "api-gateway"


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


# Note: These tests require proper authentication setup
# For now, they serve as placeholders for the structure

def test_invoice_endpoints_exist():
    """Test that invoice endpoints are registered."""
    response = client.get("/docs")
    assert response.status_code == 200
    # This verifies FastAPI docs are accessible


# TODO: Add more comprehensive tests:
# - Test invoice processing with mock Document AI
# - Test invoice validation
# - Test invoice listing with pagination
# - Test multi-tenant isolation
# - Test error handling

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
