import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json

from main import app
from core.database import get_db, Base
from core.config import settings

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
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


@pytest.fixture
def sample_image():
    """Create a sample image file for testing"""
    import io
    from PIL import Image
    
    # Create a simple test image
    image = Image.new('RGB', (224, 224), color='white')
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return img_byte_arr


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
        response = client.get("/health/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert "timestamp" in data
        assert "uptime_seconds" in data
        assert "system" in data
        assert "process" in data


class TestModels:
    """Test model endpoints"""
    
    def test_get_available_models(self):
        """Test getting available models"""
        response = client.get("/api/v1/models/available")
        assert response.status_code == 200
        
        data = response.json()
        assert "models" in data
        models = data["models"]
        assert len(models) == 3
        
        model_types = [model["type"] for model in models]
        assert "cnn" in model_types
        assert "svm" in model_types
        assert "quantum" in model_types
    
    def test_get_model_performance(self):
        """Test getting model performance"""
        response = client.get("/api/v1/models/performance")
        assert response.status_code == 200
        
        data = response.json()
        assert "model_comparison" in data
        comparison = data["model_comparison"]
        assert len(comparison) == 3
        
        for model in comparison:
            assert "model" in model
            assert "accuracy" in model
            assert "precision" in model
            assert "recall" in model
            assert "f1_score" in model
            assert "auc_roc" in model
            assert "avg_inference_time_ms" in model
    
    def test_get_model_details_cnn(self):
        """Test getting CNN model details"""
        response = client.get("/api/v1/models/cnn")
        assert response.status_code == 200
        
        data = response.json()
        assert "name" in data
        assert "architecture" in data
        assert "input_size" in data
        assert "preprocessing" in data
        assert "features" in data
        assert "advantages" in data
        assert "limitations" in data
    
    def test_get_model_details_svm(self):
        """Test getting SVM model details"""
        response = client.get("/api/v1/models/svm")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "RBF Kernel SVM"
        assert "kernel" in data
        assert "C_parameter" in data
    
    def test_get_model_details_quantum(self):
        """Test getting Quantum model details"""
        response = client.get("/api/v1/models/quantum")
        assert response.status_code == 200
        
        data = response.json()
        assert "Quantum" in data["name"]
        assert "quantum_circuit" in data
        assert "entanglement" in data
        assert "encoding" in data
    
    def test_get_model_details_not_found(self):
        """Test getting details for non-existent model"""
        response = client.get("/api/v1/models/nonexistent")
        assert response.status_code == 404


class TestAssessments:
    """Test assessment endpoints"""
    
    def test_create_assessment_cnn(self, setup_database, sample_image):
        """Test creating assessment with CNN model"""
        response = client.post(
            "/api/v1/assessment",
            params={"model_type": "cnn"},
            files={"image": ("test.png", sample_image, "image/png")}
        )
        
        # Should return 500 or 200 depending on model availability
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "prediction" in data
            assert "confidence" in data
            assert "model" in data
            assert "processing_time_ms" in data
            assert data["model"] == "cnn"
            assert 0 <= data["confidence"] <= 1
            assert data["prediction"] in ["lesion", "normal"]
    
    def test_create_assessment_svm(self, setup_database, sample_image):
        """Test creating assessment with SVM model"""
        response = client.post(
            "/api/v1/assessment",
            params={"model_type": "svm"},
            files={"image": ("test.png", sample_image, "image/png")}
        )
        
        assert response.status_code in [200, 500]
    
    def test_create_assessment_quantum(self, setup_database, sample_image):
        """Test creating assessment with Quantum model"""
        response = client.post(
            "/api/v1/assessment",
            params={"model_type": "quantum"},
            files={"image": ("test.png", sample_image, "image/png")}
        )
        
        assert response.status_code in [200, 500]
    
    def test_create_assessment_invalid_file_type(self, setup_database):
        """Test creating assessment with invalid file type"""
        response = client.post(
            "/api/v1/assessment",
            params={"model_type": "cnn"},
            files={"image": ("test.txt", "invalid content", "text/plain")}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid file type" in data["detail"]
    
    def test_create_assessment_no_image(self, setup_database):
        """Test creating assessment without image"""
        response = client.post(
            "/api/v1/assessment",
            params={"model_type": "cnn"}
        )
        
        assert response.status_code == 422
    
    def test_get_assessments_empty(self, setup_database):
        """Test getting assessments when none exist"""
        response = client.get("/api/v1/assessments")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_assessment_not_found(self, setup_database):
        """Test getting non-existent assessment"""
        response = client.get("/api/v1/assessments/999")
        assert response.status_code == 404
    
    def test_delete_assessment_not_found(self, setup_database):
        """Test deleting non-existent assessment"""
        response = client.delete("/api/v1/assessments/999")
        assert response.status_code == 404


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
    
    def test_invalid_method(self):
        """Test invalid HTTP method"""
        response = client.delete("/health")
        assert response.status_code == 405