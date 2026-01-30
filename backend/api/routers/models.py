from fastapi import APIRouter
from ..api.schemas.schemas import ModelPerformance

router = APIRouter(prefix="/api/v1", tags=["models"])


@router.get("/models/available")
async def get_available_models():
    """Get list of available models"""
    return {
        "models": [
            {
                "type": "cnn",
                "name": "ResNet-18 CNN",
                "description": "Classical Convolutional Neural Network for image classification",
                "accuracy": 0.942,
                "processing_time_ms": 200,
                "quantum_enhanced": False
            },
            {
                "type": "svm", 
                "name": "RBF Kernel SVM",
                "description": "Support Vector Machine with RBF kernel",
                "accuracy": 0.918,
                "processing_time_ms": 400,
                "quantum_enhanced": False
            },
            {
                "type": "quantum",
                "name": "Quantum Kernel SVM",
                "description": "Hybrid Quantum-Classical kernel method",
                "accuracy": 0.965,
                "processing_time_ms": 800,
                "quantum_enhanced": True
            }
        ]
    }


@router.get("/models/performance")
async def get_model_performance():
    """Get performance metrics for all models"""
    return {
        "model_comparison": [
            {
                "model": "CNN",
                "accuracy": 0.942,
                "precision": 0.938,
                "recall": 0.946,
                "f1_score": 0.942,
                "auc_roc": 0.987,
                "avg_inference_time_ms": 200,
                "training_time_hours": 4.5
            },
            {
                "model": "SVM",
                "accuracy": 0.918,
                "precision": 0.915,
                "recall": 0.921,
                "f1_score": 0.918,
                "auc_roc": 0.976,
                "avg_inference_time_ms": 400,
                "training_time_hours": 2.1
            },
            {
                "model": "Quantum",
                "accuracy": 0.965,
                "precision": 0.962,
                "recall": 0.968,
                "f1_score": 0.965,
                "auc_roc": 0.992,
                "avg_inference_time_ms": 800,
                "training_time_hours": 6.8
            }
        ]
    }


@router.get("/models/{model_type}")
async def get_model_details(model_type: str):
    """Get detailed information about a specific model"""
    
    model_details = {
        "cnn": {
            "name": "ResNet-18 CNN",
            "architecture": "Residual Neural Network",
            "input_size": [224, 224, 3],
            "num_parameters": 11689512,
            "training_dataset": "10,000 radiographs",
            "validation_dataset": "2,000 radiographs",
            "test_dataset": "2,000 radiographs",
            "preprocessing": [
                "Histogram equalization",
                "ROI extraction",
                "Data augmentation"
            ],
            "features": "Deep learned features from convolutional layers",
            "advantages": [
                "Fast inference",
                "Robust to variations",
                "End-to-end learning"
            ],
            "limitations": [
                "Requires large training dataset",
                "Black box interpretability"
            ]
        },
        "svm": {
            "name": "RBF Kernel SVM",
            "architecture": "Support Vector Machine",
            "input_features": 128,
            "kernel": "Radial Basis Function (RBF)",
            "C_parameter": 1.0,
            "gamma": "scale",
            "training_dataset": "8,000 radiographs",
            "validation_dataset": "1,000 radiographs",
            "test_dataset": "1,000 radiographs",
            "preprocessing": [
                "GLCM texture features",
                "LBP features",
                "Intensity histogram"
            ],
            "features": "Hand-crafted texture and intensity features",
            "advantages": [
                "Good with small datasets",
                "Interpretable decision boundary",
                "Fast training"
            ],
            "limitations": [
                "Requires feature engineering",
                "Sensitive to parameter tuning"
            ]
        },
        "quantum": {
            "name": "Quantum Kernel SVM",
            "architecture": "Quantum-Classical Hybrid",
            "quantum_circuit": "4-qubit variational circuit",
            "entanglement": "Linear entanglement",
            "encoding": "Angle encoding",
            "quantum_shots": 1024,
            "training_dataset": "5,000 radiographs",
            "validation_dataset": "500 radiographs",
            "test_dataset": "500 radiographs",
            "preprocessing": [
                "Feature selection (PCA)",
                "Quantum encoding",
                "Classical post-processing"
            ],
            "features": "Quantum kernel matrix over classical features",
            "advantages": [
                "Higher dimensional feature space",
                "Quantum speedup potential",
                "Novel feature correlations"
            ],
            "limitations": [
                "Higher computational cost",
                "Limited qubit count",
                "Quantum noise sensitivity"
            ]
        }
    }
    
    if model_type not in model_details:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Model not found")
    
    return model_details[model_type]