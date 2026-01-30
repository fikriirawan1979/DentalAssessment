import os
from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "DentalAssessment API"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str = "postgresql://dental_user:dental_password@localhost:5432/dental_db"
    database_pool_size: int = 20
    database_max_overflow: int = 30
    test_database_url: Optional[str] = None
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_pool_size: int = 10
    
    # MinIO/S3
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_name: str = "dental-images"
    minio_secure: bool = False
    
    # Security
    secret_key: str = "your-super-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Model Configuration
    model_dir: str = "./models"
    max_file_size: int = 10485760  # 10MB
    allowed_file_types: List[str] = ["image/jpeg", "image/png", "image/tiff"]
    
    # Quantum Configuration
    quantum_backend: str = "default.qubit"
    quantum_shots: int = 1024
    quantum_threads: int = 4
    quantum_noise_model: bool = False
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_to_file: bool = False
    log_file_path: str = "./logs/app.log"
    
    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080"
    ]
    
    # Performance
    cache_ttl: int = 3600  # 1 hour
    max_concurrent_requests: int = 100
    request_timeout: int = 30
    
    # Development
    enable_profiling: bool = False
    enable_debug_routes: bool = False
    auto_reload: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()