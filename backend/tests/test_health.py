import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from core.database import get_db, Base

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture(scope="module")
def setup_database():
    """Setup test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestHealth:
    """Test health endpoints"""
    
    def test_health_check(self, setup_database):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "services" in data
        assert "uptime_seconds" in data
    
    def test_readiness_check(self):
        """Test readiness probe"""
        response = client.get("/health/ready")
        assert response.status_code == 200
        
        data = response.json()
        assert "ready" in data
        assert "timestamp" in data
    
    def test_liveness_check(self):
        """Test liveness probe"""
        response = client.get("/health/live")
        assert response.status_code == 200
        
        data = response.json()
        assert "alive" in data
        assert "timestamp" in data
    
    def test_metrics(self):
        """Test metrics endpoint"""
        response = client.get("/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert "timestamp" in data
        assert "uptime_seconds" in data
        assert "system" in data
        assert "process" in data


class TestRoot:
    """Test root endpoint"""
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "description" in data
        assert "docs" in data
        assert "health" in data
        assert "status" in data
        assert data["status"] == "operational"


class TestErrorHandling:
    """Test error handling"""
    
    def test_404_endpoint(self):
        """Test 404 error handling"""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404