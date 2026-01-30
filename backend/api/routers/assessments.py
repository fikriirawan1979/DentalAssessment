from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import json
import time
from datetime import datetime

from ..core.database import get_db
from ..core.models import Assessment
from ..api.schemas.schemas import (
    AssessmentRequest, AssessmentResponse, ModelType, PredictionType,
    ImageInfo, ROIInfo, FeatureExtractionResult
)
from ..services.model_orchestrator import ModelOrchestrator
from ..services.image_service import ImageService
from ..services.logging_service import LoggingService

router = APIRouter(prefix="/api/v1", tags=["assessments"])

# Initialize services
model_orchestrator = ModelOrchestrator()
image_service = ImageService()
logging_service = LoggingService()


@router.post("/assessment", response_model=AssessmentResponse)
async def create_assessment(
    background_tasks: BackgroundTasks,
    model_type: ModelType,
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Create a new dental assessment
    
    - **model_type**: Type of model to use (cnn, svm, quantum)
    - **image**: Dental radiograph image file
    """
    
    # Validate image file
    if not image.content_type in ["image/jpeg", "image/png", "image/tiff"]:
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Only JPEG, PNG, and TIFF are supported."
        )
    
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # Save uploaded image
        image_info = await image_service.save_uploaded_image(image, request_id)
        
        # Log the request
        await logging_service.log_request(
            request_id=request_id,
            model_type=model_type.value,
            image_filename=image_info.filename
        )
        
        # Perform assessment using the specified model
        result = await model_orchestrator.assess_image(
            image_path=image_info.path,
            model_type=model_type,
            request_id=request_id
        )
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000
        
        # Save assessment to database
        db_assessment = Assessment(
            image_filename=image_info.filename,
            image_path=image_info.path,
            image_size=image_info.size,
            image_format=image_info.format,
            model_type=model_type.value,
            prediction=result.prediction.value,
            confidence=result.confidence,
            processing_time_ms=processing_time,
            roi_coordinates=result.roi_coordinates,
            features=result.features_dict,
            created_at=datetime.utcnow()
        )
        
        db.add(db_assessment)
        db.commit()
        db.refresh(db_assessment)
        
        # Prepare response
        response = AssessmentResponse(
            id=db_assessment.id,
            prediction=result.prediction,
            confidence=result.confidence,
            model=model_type,
            processing_time_ms=processing_time,
            roi_image=result.roi_base64,
            features=result.features_dict
        )
        
        # Add background task for cleanup if needed
        background_tasks.add_task(
            logging_service.log_completion,
            request_id=request_id,
            assessment_id=db_assessment.id,
            success=True
        )
        
        return response
        
    except Exception as e:
        # Log error
        await logging_service.log_error(
            request_id=request_id,
            error_message=str(e),
            error_type=type(e).__name__
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Assessment failed: {str(e)}"
        )


@router.get("/assessments", response_model=List[AssessmentResponse])
async def get_assessments(
    skip: int = 0,
    limit: int = 100,
    model_type: Optional[ModelType] = None,
    db: Session = Depends(get_db)
):
    """Get list of assessments with optional filtering"""
    
    query = db.query(Assessment)
    
    if model_type:
        query = query.filter(Assessment.model_type == model_type.value)
    
    assessments = query.offset(skip).limit(limit).all()
    
    return [
        AssessmentResponse(
            id=assessment.id,
            prediction=PredictionType(assessment.prediction),
            confidence=assessment.confidence,
            model=ModelType(assessment.model_type),
            processing_time_ms=assessment.processing_time_ms,
            features=assessment.features
        )
        for assessment in assessments
    ]


@router.get("/assessments/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(assessment_id: int, db: Session = Depends(get_db)):
    """Get a specific assessment by ID"""
    
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    return AssessmentResponse(
        id=assessment.id,
        prediction=PredictionType(assessment.prediction),
        confidence=assessment.confidence,
        model=ModelType(assessment.model_type),
        processing_time_ms=assessment.processing_time_ms,
        roi_image=None,  # ROI image not stored in DB for space efficiency
        features=assessment.features
    )


@router.delete("/assessments/{assessment_id}")
async def delete_assessment(assessment_id: int, db: Session = Depends(get_db)):
    """Delete an assessment by ID"""
    
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    # Delete associated image file
    await image_service.delete_image(assessment.image_path)
    
    # Delete database record
    db.delete(assessment)
    db.commit()
    
    return {"message": "Assessment deleted successfully"}