"""Backup utilities for cost tracking."""

import os
from typing import Optional
from loguru import logger
import sherpa_ai.config as cfg


class DatabaseBackup:
    """Database backup manager."""
    
    def __init__(
        self,
        local_file_path: str,
        bucket_name: Optional[str] = None,
        s3_file_key: Optional[str] = None
    ):
        """Initialize the database backup manager."""
        self.local_file_path = local_file_path
        self.bucket_name = bucket_name
        self.s3_file_key = s3_file_key
        self.log_to_s3 = bool(self.bucket_name and self.s3_file_key)
        
        if self.log_to_s3:
            try:
                import boto3
                self.s3_client = boto3.client("s3")
            except ImportError:
                logger.error("Could not import boto3. S3 backup will be disabled.")
                self.s3_client = None
                self.log_to_s3 = False
        else:
            self.s3_client = None
    
    def upload_to_s3(self):
        """Upload database file to S3 if enabled."""
        if not self.log_to_s3 or not self.s3_client:
            return

        if not os.path.exists(self.local_file_path):
            logger.warning(f"Local database file not found at {self.local_file_path}. Skipping S3 upload.")
            return

        try:
            self.s3_client.upload_file(self.local_file_path, self.bucket_name, self.s3_file_key)
        except Exception as e:
            logger.error(f"Error uploading database to S3: {str(e)}")
    
    def download_from_s3(self):
        """Download database file from S3 if enabled."""
        if not self.log_to_s3 or not self.s3_client:
            return

        try:
            self.s3_client.download_file(self.bucket_name, self.s3_file_key, self.local_file_path)
        except Exception as e:
            logger.error(f"Error downloading database from S3: {str(e)}")
    
