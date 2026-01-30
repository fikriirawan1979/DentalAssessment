from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ModelType(str, Enum):
    """Available model types"""
    CNN = "cnn"
    SVM = "svm"
    QUANTUM = "quantum"


class PredictionType(str, Enum):
    """Prediction results"""
    LESION = "lesion"
    NORMAL = "normal"


class AssessmentRequest(BaseModel):
    """Request model for dental assessment"""
    model_type: ModelType = Field(..., description="Type of model to use for prediction")
    
    class Config:
        use_enum_values = True


class AssessmentResponse(BaseModel):
    """Response model for dental assessment"""
    id: int
    prediction: PredictionType
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    model: ModelType
    processing_time_ms: float
    roi_image: Optional[str] = Field(None, description="Base64 encoded ROI image")
    features: Optional[Dict[str, Any]] = Field(None, description="Extracted features")
    
    class Config:
        use_enum_values = True


class ImageInfo(BaseModel):
    """Image information model"""
    filename: str
    size: int
    format: str
    dimensions: Optional[Dict[str, int]] = None
    quality_score: Optional[float] = None


class ROIInfo(BaseModel):
    """Region of Interest information"""
    coordinates: Dict[str, int]
    dimensions: Dict[str, int]
    extraction_method: str


class FeatureExtractionResult(BaseModel):
    """Feature extraction results"""
    texture_features: Dict[str, float]
    intensity_features: Dict[str, float]
    shape_features: Dict[str, float]
    spectral_features: Optional[Dict[str, float]] = None


class ModelPerformance(BaseModel):
    """Model performance metrics"""
    model_type: ModelType
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    auc_roc: Optional[float] = None
    processing_time_avg: Optional[float] = None
    
    class Config:
        use_enum_values = True


class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str]
    uptime_seconds: float


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime


class BatchAssessmentRequest(BaseModel):
    """Batch assessment request"""
    model_type: ModelType
    max_concurrent: int = Field(default=5, ge=1, le=10)
    
    class Config:
        use_enum_values = True


class BatchAssessmentResponse(BaseModel):
    """Batch assessment response"""
    results: List[AssessmentResponse]
    total_processed: int
    total_failed: int
    total_time_ms: float
    average_confidence: Optional[float] = None