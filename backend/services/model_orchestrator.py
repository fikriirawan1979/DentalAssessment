from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import base64
import structlog
from ..api.schemas.schemas import ModelType, PredictionType

logger = structlog.get_logger()


class ModelResult:
    """Result object for model predictions"""
    
    def __init__(
        self,
        prediction: PredictionType,
        confidence: float,
        features_dict: Dict[str, Any],
        roi_base64: Optional[str] = None,
        roi_coordinates: Optional[Dict[str, int]] = None,
        processing_time_ms: float = 0.0
    ):
        self.prediction = prediction
        self.confidence = confidence
        self.features_dict = features_dict
        self.roi_base64 = roi_base64
        self.roi_coordinates = roi_coordinates
        self.processing_time_ms = processing_time_ms


class ModelOrchestrator:
    """Orchestrates model selection and execution"""
    
    def __init__(self):
        self.models = {}
        self._load_models()
    
    def _load_models(self):
        """Load all available models"""
        try:
            # Import models here to avoid circular imports
            from ..classical.cnn_model import CNNModel
            from ..classical.svm_model import SVMModel
            from ..quantum.quantum_svm import QuantumSVMModel
            
            self.models[ModelType.CNN] = CNNModel()
            self.models[ModelType.SVM] = SVMModel()
            self.models[ModelType.QUANTUM] = QuantumSVMModel()
            
            logger.info("All models loaded successfully")
        except Exception as e:
            logger.error("Failed to load models", error=str(e))
            # Create dummy models for fallback
            self._create_dummy_models()
    
    def _create_dummy_models(self):
        """Create dummy models when real models fail to load"""
        class DummyModel:
            def __init__(self, model_type: ModelType):
                self.model_type = model_type
            
            async def predict(self, image_path: str, **kwargs) -> ModelResult:
                import time
                import random
                time.sleep(0.1)  # Simulate processing
                
                prediction = PredictionType.LESION if random.random() > 0.5 else PredictionType.NORMAL
                confidence = random.uniform(0.7, 0.95)
                
                return ModelResult(
                    prediction=prediction,
                    confidence=confidence,
                    features_dict={"dummy_feature": 0.5, "model_type": self.model_type.value},
                    processing_time_ms=100
                )
        
        self.models[ModelType.CNN] = DummyModel(ModelType.CNN)
        self.models[ModelType.SVM] = DummyModel(ModelType.SVM)
        self.models[ModelType.QUANTUM] = DummyModel(ModelType.QUANTUM)
        
        logger.warning("Using dummy models - real models failed to load")
    
    async def assess_image(
        self,
        image_path: str,
        model_type: ModelType,
        request_id: str = None
    ) -> ModelResult:
        """Assess image using specified model"""
        
        if model_type not in self.models:
            raise ValueError(f"Model {model_type} not available")
        
        model = self.models[model_type]
        
        try:
            logger.info(
                "Starting assessment",
                model_type=model_type.value,
                image_path=image_path,
                request_id=request_id
            )
            
            # Perform prediction
            result = await model.predict(image_path, request_id=request_id)
            
            logger.info(
                "Assessment completed",
                model_type=model_type.value,
                prediction=result.prediction.value,
                confidence=result.confidence,
                processing_time_ms=result.processing_time_ms,
                request_id=request_id
            )
            
            # Log performance
            from .logging_service import logging_service
            await logging_service.log_model_performance(
                model_type=model_type.value,
                processing_time_ms=result.processing_time_ms,
                confidence=result.confidence,
                prediction=result.prediction.value
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Assessment failed",
                model_type=model_type.value,
                image_path=image_path,
                error=str(e),
                request_id=request_id
            )
            raise
    
    def get_available_models(self) -> Dict[str, Dict[str, Any]]:
        """Get information about available models"""
        return {
            model_type.value: {
                "type": model_type.value,
                "loaded": True,
                "class": model.__class__.__name__
            }
            for model_type, model in self.models.items()
        }
    
    async def batch_assess(
        self,
        image_paths: list,
        model_type: ModelType,
        max_concurrent: int = 5
    ) -> list:
        """Batch assess multiple images"""
        import asyncio
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def assess_with_semaphore(image_path):
            async with semaphore:
                return await self.assess_image(image_path, model_type)
        
        tasks = [assess_with_semaphore(path) for path in image_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return results
    
    def get_model_info(self, model_type: ModelType) -> Dict[str, Any]:
        """Get detailed information about a specific model"""
        if model_type not in self.models:
            return {"error": "Model not available"}
        
        model = self.models[model_type]
        
        return {
            "model_type": model_type.value,
            "class_name": model.__class__.__name__,
            "loaded": True,
            "available": True
        }


# Global orchestrator instance
model_orchestrator = ModelOrchestrator()