from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from ..core.database import Base


class Assessment(Base):
    """Assessment model for storing dental radiograph analysis results"""
    
    __tablename__ = "assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(50), nullable=True, index=True)
    image_filename = Column(String(255), nullable=False)
    image_path = Column(String(500), nullable=False)
    image_size = Column(Integer, nullable=False)
    image_format = Column(String(10), nullable=False)
    
    # Model results
    model_type = Column(String(20), nullable=False)  # cnn, svm, quantum
    prediction = Column(String(10), nullable=False)  # lesion, normal
    confidence = Column(Float, nullable=False)
    processing_time_ms = Column(Float, nullable=False)
    
    # ROI information
    roi_coordinates = Column(JSON, nullable=True)
    roi_size = Column(JSON, nullable=True)
    
    # Feature extraction results
    features = Column(JSON, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Quality metrics
    image_quality_score = Column(Float, nullable=True)
    blur_detected = Column(Boolean, default=False)
    contrast_score = Column(Float, nullable=True)


class ModelPerformance(Base):
    """Model performance tracking for analytics"""
    
    __tablename__ = "model_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    model_type = Column(String(20), nullable=False)
    version = Column(String(20), nullable=False)
    
    # Performance metrics
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    auc_roc = Column(Float, nullable=True)
    
    # Training metrics
    training_loss = Column(Float, nullable=True)
    validation_loss = Column(Float, nullable=True)
    training_time_hours = Column(Float, nullable=True)
    
    # Dataset info
    training_samples = Column(Integer, nullable=True)
    validation_samples = Column(Integer, nullable=True)
    test_samples = Column(Integer, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)


class SystemLog(Base):
    """System logging for monitoring and debugging"""
    
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(10), nullable=False)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message = Column(Text, nullable=False)
    module = Column(String(50), nullable=True)
    function = Column(String(50), nullable=True)
    
    # Request context
    request_id = Column(String(50), nullable=True)
    user_id = Column(String(50), nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    # Additional context
    context = Column(JSON, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())