from minio import Minio
from minio.error import S3Error
from typing import Optional, BinaryIO
import os
import uuid
import structlog
from ..core.config import settings

logger = structlog.get_logger()


class ImageService:
    """Service for handling image storage and retrieval"""
    
    def __init__(self):
        self.minio_client: Optional[Minio] = None
        self.bucket_name = settings.minio_bucket_name
    
    async def initialize(self):
        """Initialize MinIO client and bucket"""
        try:
            self.minio_client = Minio(
                settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_secure
            )
            
            # Create bucket if it doesn't exist
            if not self.minio_client.bucket_exists(self.bucket_name):
                self.minio_client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
            
            logger.info("MinIO client initialized")
        except Exception as e:
            logger.error("Failed to initialize MinIO", error=str(e))
            self.minio_client = None
    
    async def save_uploaded_image(self, file, request_id: str) -> dict:
        """Save uploaded image to MinIO and local filesystem"""
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{request_id}_{file.filename}"
        
        # Create local directory if it doesn't exist
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save to local filesystem for immediate processing
        local_path = os.path.join(upload_dir, unique_filename)
        
        try:
            # Read file content
            content = await file.read()
            
            # Save locally
            with open(local_path, "wb") as f:
                f.write(content)
            
            # Save to MinIO if available
            if self.minio_client:
                from io import BytesIO
                file_stream = BytesIO(content)
                file_length = len(content)
                
                self.minio_client.put_object(
                    self.bucket_name,
                    unique_filename,
                    file_stream,
                    file_length,
                    content_type=file.content_type
                )
                logger.info("Image saved to MinIO", filename=unique_filename)
            
            return {
                "filename": unique_filename,
                "path": local_path,
                "size": len(content),
                "format": file.content_type
            }
            
        except Exception as e:
            logger.error("Failed to save image", filename=file.filename, error=str(e))
            raise
    
    async def get_image(self, filename: str) -> Optional[bytes]:
        """Get image data from MinIO or local filesystem"""
        
        # Try MinIO first
        if self.minio_client:
            try:
                response = self.minio_client.get_object(self.bucket_name, filename)
                data = response.read()
                response.close()
                response.release_conn()
                return data
            except S3Error:
                logger.warning("Image not found in MinIO", filename=filename)
        
        # Fallback to local filesystem
        local_path = os.path.join("uploads", filename)
        if os.path.exists(local_path):
            try:
                with open(local_path, "rb") as f:
                    return f.read()
            except Exception as e:
                logger.error("Failed to read local image", path=local_path, error=str(e))
        
        return None
    
    async def delete_image(self, filename: str) -> bool:
        """Delete image from MinIO and local filesystem"""
        
        success = True
        
        # Delete from MinIO
        if self.minio_client:
            try:
                self.minio_client.remove_object(self.bucket_name, filename)
                logger.info("Image deleted from MinIO", filename=filename)
            except S3Error as e:
                logger.warning("Failed to delete from MinIO", filename=filename, error=str(e))
                success = False
        
        # Delete from local filesystem
        local_path = os.path.join("uploads", filename)
        if os.path.exists(local_path):
            try:
                os.remove(local_path)
                logger.info("Image deleted locally", path=local_path)
            except Exception as e:
                logger.warning("Failed to delete local image", path=local_path, error=str(e))
                success = False
        
        return success
    
    async def get_image_info(self, filename: str) -> Optional[dict]:
        """Get image information from MinIO"""
        
        if not self.minio_client:
            return None
        
        try:
            stat = self.minio_client.stat_object(self.bucket_name, filename)
            return {
                "filename": filename,
                "size": stat.size,
                "last_modified": stat.last_modified,
                "content_type": stat.content_type,
                "etag": stat.etag
            }
        except S3Error:
            return None
    
    async def list_images(self) -> list:
        """List all images in the bucket"""
        
        if not self.minio_client:
            return []
        
        try:
            objects = self.minio_client.list_objects(self.bucket_name)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            logger.error("Failed to list images", error=str(e))
            return []


# Global image service instance
image_service = ImageService()