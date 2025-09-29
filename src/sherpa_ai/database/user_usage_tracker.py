"""User usage tracking module for Sherpa AI."""

import json
import time
from typing import Dict, Any, Optional, List
from sqlalchemy import Boolean, Column, Integer, String, Float, Text, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import declarative_base, sessionmaker

import sherpa_ai.config as cfg
from sherpa_ai.cost_tracking.pricing import PricingManager
from sherpa_ai.cost_tracking.logger import UsageLogger
from sherpa_ai.cost_tracking.backup import DatabaseBackup
from loguru import logger

Base = declarative_base()


class UsageTracker(Base):
    """SQLAlchemy model for tracking LLM token usage."""
    __tablename__ = "usage_tracker"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    cost = Column(Float, default=0.0)
    model_name = Column(String, default="unknown")
    session_id = Column(String, default=None)
    agent_name = Column(String, default=None)
    timestamp = Column(Integer, default=lambda: int(time.time()))
    reset_timestamp = Column(Boolean, default=False)
    reminded_timestamp = Column(Boolean, default=False)
    usage_metadata_json = Column(Text, default=None)


class Whitelist(Base):
    """SQLAlchemy model for user whitelist."""
    __tablename__ = "whitelist"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False, unique=True)


class UserUsageTracker:
    """Clean, minimal usage tracker with essential functionality only."""

    def __init__(
        self,
        db_name: str = cfg.DB_NAME,
        db_url: str = cfg.DB_URL,
        bucket_name: Optional[str] = None,
        s3_file_key: Optional[str] = None,
        log_to_s3: bool = None,
        log_to_file: bool = None,
        log_file_path: Optional[str] = None,
        pricing_manager: Optional[PricingManager] = None,
        engine: Optional[Any] = None,
        session: Optional[Any] = None,
        verbose_logger: Optional[Any] = None,
    ):
        """Initialize the clean UserUsageTracker."""
        self.db_name = db_name
        self.db_url = db_url
        
        # Use provided engine/session or create new ones
        if engine is not None:
            self.engine = engine
        else:
            self.engine = create_engine(self.db_url)
            
        if session is not None:
            self.session = session
        else:
            Session = sessionmaker(bind=self.engine)
            self.session = Session()

        # Set attributes expected by tests
        self.s3_file_key = s3_file_key or "token_counter.db"
        self.bucket_name = bucket_name or "sherpa-sqlight"
        self.local_file_path = f"./{self.db_name}"
        
        # Create default verbose logger if none provided
        if verbose_logger is None:
            from sherpa_ai.verbose_loggers.base import BaseVerboseLogger
            class DefaultVerboseLogger(BaseVerboseLogger):
                def log(self, message):
                    pass
            self.verbose_logger = DefaultVerboseLogger()
        else:
            self.verbose_logger = verbose_logger

        # Create tables
        Base.metadata.create_all(self.engine)
        
        # Configuration
        self.max_daily_token = cfg.DAILY_TOKEN_LIMIT
        self.limit_time_size_in_hours = float(cfg.LIMIT_TIME_SIZE_IN_HOURS or 24)
        
        # Initialize helpers
        self.pricing_manager = pricing_manager or PricingManager()
        self.usage_logger = UsageLogger(
            log_to_file if log_to_file is not None else cfg.USAGE_LOG_TO_FILE, 
            log_file_path or cfg.USAGE_LOG_FILE_PATH
        )
        # Use config defaults if not explicitly set
        use_s3 = log_to_s3 if log_to_s3 is not None else cfg.USAGE_LOG_TO_S3
        # Use default bucket and key if S3 is enabled but not explicitly provided
        default_bucket = bucket_name or "sherpa-sqlight"
        default_key = s3_file_key or "token_counter.db"
        self.database_backup = DatabaseBackup(
            local_file_path=f"./{self.db_name}",
            bucket_name=default_bucket if use_s3 else None,
            s3_file_key=default_key if use_s3 else None
        )
    
    def add_usage(
        self, 
        user_id: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        usage_metadata: Optional[Dict[str, Any]] = None,
        model_name: Optional[str] = None,
        session_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        cost: Optional[float] = None,
        check_limits: bool = True,
        send_reminder: bool = True,
        reset_timestamp: bool = False,
        reminded_timestamp: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Unified method to add usage data with optional limit checking.

        Args:
            user_id: ID of the user.
            input_tokens: Number of input tokens (used if no usage_metadata).
            output_tokens: Number of output tokens (used if no usage_metadata).
            usage_metadata: Usage metadata from callback.
            model_name: Name of the model used.
            session_id: ID of the session.
            agent_name: Name of the agent.
            cost: Cost in USD. If None, will be calculated.
            check_limits: Whether to check if user has exceeded limits.
            send_reminder: Whether to send reminder if approaching limits.
            reset_timestamp: Whether to reset the timestamp.
            reminded_timestamp: Whether to mark as reminded.
            
        Returns:
            dict: Usage information if check_limits=True, None otherwise.
        """
        # Extract token information from usage_metadata if provided
        if usage_metadata:
            input_tokens, output_tokens, total_cost = self._extract_token_info(usage_metadata, model_name)
            if cost is None:
                cost = total_cost
        else:
            # Use provided tokens directly
            if cost is None and model_name:
                cost = self.pricing_manager.calculate_cost(model_name, input_tokens, output_tokens)
            elif cost is None:
                cost = 0.0
        
        # Store data
        if usage_metadata is None:
            # Create usage_metadata from tokens for proper tracking
            usage_metadata = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            }
        usage_metadata_json = json.dumps(usage_metadata)
        
        try:
            # Try with usage_metadata_json column
            data = UsageTracker(
                user_id=user_id,
                cost=cost,
                model_name=model_name or "unknown",
                session_id=session_id,
                agent_name=agent_name,
                reset_timestamp=reset_timestamp,
                reminded_timestamp=reminded_timestamp,
                usage_metadata_json=usage_metadata_json
            )
            self.session.add(data)
            self.session.commit()
        except Exception as e:
            # Handle case where database doesn't have usage_metadata_json column
            if "usage_metadata_json" in str(e):
                # Retry without usage_metadata_json
                self.session.rollback()
                data = UsageTracker(
                    user_id=user_id,
                    cost=cost,
                    model_name=model_name or "unknown",
                    session_id=session_id,
                    agent_name=agent_name,
                    reset_timestamp=reset_timestamp,
                    reminded_timestamp=reminded_timestamp
                )
                self.session.add(data)
                self.session.commit()
            else:
                raise
        
        # Log usage
        self.usage_logger.log_usage(
            user_id=user_id,
            cost=cost,
            model_name=model_name or "unknown",
            session_id=session_id,
            agent_name=agent_name,
            usage_metadata=usage_metadata
        )
        
        # Backup to S3
        self.database_backup.upload_to_s3()
        
        # Handle limit checking and reminders
        if check_limits:
            result = self.check_usage(user_id, input_tokens, output_tokens, usage_metadata)
            if send_reminder:
                self._send_reminder(user_id)
            return result
        
        if send_reminder:
            self._send_reminder(user_id)
        
        return None
    
    def _extract_token_info(self, usage_metadata: Dict[str, Any], model_name: Optional[str] = None) -> tuple[int, int, float]:
        """Extract token information from usage metadata (flat or complex)."""
        # Check if it's complex metadata (has model keys)
        if any(isinstance(v, dict) for v in usage_metadata.values()):
            # Complex metadata: {"gpt-4o": {"input_tokens": 100, "output_tokens": 50}}
            total_input_tokens = 0
            total_output_tokens = 0
            total_cost = 0.0
            
            for model_key, model_usage in usage_metadata.items():
                if isinstance(model_usage, dict):
                    input_tokens = model_usage.get("input_tokens", 0)
                    output_tokens = model_usage.get("output_tokens", 0)
                    
                    # Extract base model name
                    base_model_name = model_key.split("-")[0] + "-" + model_key.split("-")[1] if "-" in model_key else model_key
                    
                    # Calculate cost for this model
                    model_cost = self.pricing_manager.calculate_cost(base_model_name, input_tokens, output_tokens)
                    total_cost += model_cost
                    
                    total_input_tokens += input_tokens
                    total_output_tokens += output_tokens
            
            return total_input_tokens, total_output_tokens, total_cost
        else:
            # Flat metadata: {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150}
            input_tokens = usage_metadata.get("input_tokens", 0)
            output_tokens = usage_metadata.get("output_tokens", 0)
            
            # Calculate cost
            if model_name:
                cost = self.pricing_manager.calculate_cost(model_name, input_tokens, output_tokens)
            else:
                cost = 0.0
            
            return input_tokens, output_tokens, cost
    
    def check_usage(self, user_id: str, input_tokens: int, output_tokens: int, usage_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Check if a user can consume more tokens."""
        # Check if user is whitelisted
        if self._is_whitelisted(user_id):
            return {
                "token-left": self.max_daily_token,
                "can_execute": True,
                "message": "User is whitelisted, no token limits applied.",
                "time_left": ""
            }
        
        # Get current usage
        current_usage = self._get_sum_of_tokens_since_last_reset(user_id)
        
        # Use total_tokens from usage_metadata if available, otherwise calculate
        if usage_metadata and "total_tokens" in usage_metadata:
            total_tokens = usage_metadata["total_tokens"]
        else:
            total_tokens = input_tokens + output_tokens
        
        # Check limits
        if total_tokens > self.max_daily_token:
            return {
                "token-left": 0,
                "can_execute": False,
                "message": "Your request exceeds token limit. Try using smaller context.",
                "time_left": ""
            }
        
        if current_usage + total_tokens > self.max_daily_token:
            return {
                "token-left": self.max_daily_token - current_usage,
                "can_execute": False,
                "message": "Daily token limit exceeded.",
                "time_left": ""
            }
        
        return {
            "token-left": self.max_daily_token - current_usage - total_tokens,
            "can_execute": True,
            "message": "",
            "time_left": ""
        }
    
    def add_to_whitelist(self, user_id: str):
        """Add a user to the whitelist."""
        try:
            whitelist_entry = Whitelist(user_id=user_id)
            self.session.add(whitelist_entry)
            self.session.commit()
        except IntegrityError:
            logger.warning(f"User {user_id} is already whitelisted")
            self.session.rollback()
        
        if not cfg.FLASK_DEBUG:
            self.database_backup.upload_to_s3()
    
    def _is_whitelisted(self, user_id: str) -> bool:
        """Check if a user is whitelisted."""
        return bool(self.session.query(Whitelist).filter_by(user_id=user_id).first())
    
    def get_all_whitelisted_ids(self) -> List[str]:
        """Get all whitelisted user IDs (backward compatibility)."""
        return [user.user_id for user in self.session.query(Whitelist).all()]
    
    def get_whitelist_by_user_id(self, user_id: str) -> List[Dict[str, Any]]:
        """Get whitelist information for a specific user (backward compatibility)."""
        data = self.session.query(Whitelist).filter_by(user_id=user_id).all()
        return [{"id": item.id, "user_id": item.user_id} for item in data]
    
    def _get_sum_of_tokens_since_last_reset(self, user_id: str) -> int:
        """Get total tokens used since last reset."""
        data = self._get_data_since_last_reset(user_id)
        if not data:
            return 0
        
        total_tokens = 0
        for record in data:
            if record.usage_metadata_json:
                try:
                    usage_metadata = json.loads(record.usage_metadata_json)
                    total_tokens += usage_metadata.get("total_tokens", 0)
                except (json.JSONDecodeError, KeyError):
                    continue
        
        return total_tokens
    
    def _get_data_since_last_reset(self, user_id: str) -> List[UsageTracker]:
        """Get data since last reset for a user."""
        return self.session.query(UsageTracker).filter_by(user_id=user_id).all()
    
    def _send_reminder(self, user_id: str):
        """Send reminder if user is approaching limits."""
        # Simple reminder logic - can be enhanced
        current_usage = self._get_sum_of_tokens_since_last_reset(user_id)
        if current_usage > self.max_daily_token * 0.75:  # 75% threshold
            message = f"Hi friend, you have used {current_usage} tokens out of {self.max_daily_token} daily limit. You are approaching your limit."
            self.verbose_logger.log(message)
            logger.info(f"User {user_id} is approaching token limit: {current_usage}/{self.max_daily_token}")
    
    def get_all_data(self) -> List[Dict[str, Any]]:
        """Get all usage data."""
        data = self.session.query(UsageTracker).all()
        return [
            {
                "id": item.id,
                "user_id": item.user_id,
                "cost": item.cost,
                "model_name": item.model_name,
                "session_id": item.session_id,
                "agent_name": item.agent_name,
                "timestamp": item.timestamp,
                "reset_timestamp": item.reset_timestamp,
                "reminded_timestamp": item.reminded_timestamp,
                "usage_metadata_json": item.usage_metadata_json
            }
            for item in data
        ]

    def parse_usage_metadata(self, usage_metadata_json: str) -> Dict[str, Any]:
        """Parse usage metadata JSON string into structured data.

        Args:
            usage_metadata_json (str): JSON string of usage metadata.

        Returns:
            Dict[str, Any]: Parsed usage metadata or empty dict if parsing fails.
        """
        if not usage_metadata_json:
            return {}
        
        try:
            return json.loads(usage_metadata_json)
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Failed to parse usage metadata JSON: {usage_metadata_json}")
            return {}
    
    def close_connection(self):
        """Close the database connection and cleanup helpers."""
        self.session.close()
    
    # Backward compatibility methods (delegate to reporting module)
    def get_tokens_from_usage_metadata(self, usage_metadata: Dict[str, Any]) -> Dict[str, int]:
        """Extract token counts from usage metadata."""
        input_tokens = usage_metadata.get("input_tokens", 0)
        output_tokens = usage_metadata.get("output_tokens", 0)
        total_tokens = usage_metadata.get("total_tokens", 0)
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens
        }
    
    def get_token_details_from_usage_metadata(self, usage_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract detailed token information from usage metadata."""
        input_details = usage_metadata.get("input_token_details", {})
        output_details = usage_metadata.get("output_token_details", {})
        return {
            "reasoning_tokens": output_details.get("reasoning", 0),
            "cache_creation": input_details.get("cache_creation", 0),
            "cache_read": input_details.get("cache_read", 0),
            "audio_tokens": input_details.get("audio", 0) + output_details.get("audio", 0)
        }
    
    def upload_to_s3(self):
        """Upload database to S3."""
        self.database_backup.upload_to_s3()
    
    @classmethod
    def download_from_s3(cls, db_name: str = None, db_url: str = None, **kwargs):
        """Download database from S3 and return UserUsageTracker instance."""
        # This is a simplified implementation for backward compatibility
        return cls(db_name=db_name, db_url=db_url, **kwargs)
    
    def download_from_s3_instance(self):
        """Download database from S3 using instance configuration."""
        self.database_backup.download_from_s3()
    
    
    
    

    def get_user_cost(self, user_id: str) -> float:
        """Get total cost for a user."""
        data = self._get_data_since_last_reset(user_id)
        return sum(record.cost for record in data)

    def get_session_cost(self, session_id: str) -> float:
        """Get total cost for a session."""
        data = self.session.query(UsageTracker).filter_by(session_id=session_id).all()
        return sum(record.cost for record in data)

    def get_agent_cost(self, agent_name: str) -> float:
        """Get total cost for an agent."""
        data = self.session.query(UsageTracker).filter_by(agent_name=agent_name).all()
        return sum(record.cost for record in data)
    
    def get_cost_summary(self, user_id: str = None) -> dict:
        """Get cost summary statistics."""
        if user_id:
            # Get summary for specific user
            data = self._get_data_since_last_reset(user_id)
            total_cost = sum(record.cost for record in data)
            
            # Calculate model breakdown
            model_breakdown = {}
            for record in data:
                model_breakdown[record.model_name] = model_breakdown.get(record.model_name, 0) + record.cost
            
            return {
                "total_cost": total_cost,
                "user_id": user_id,
                "total_records": len(data),
                "model_breakdown": model_breakdown
            }
        else:
            # Get summary for all users
            all_data = self.session.query(UsageTracker).all()
            total_cost = sum(record.cost for record in all_data)
            user_costs = {}
            model_breakdown = {}
            for record in all_data:
                user_costs[record.user_id] = user_costs.get(record.user_id, 0) + record.cost
                model_breakdown[record.model_name] = model_breakdown.get(record.model_name, 0) + record.cost

            return {
                "total_cost": total_cost,
                "user_costs": user_costs,
                "total_records": len(all_data),
                "model_breakdown": model_breakdown
            }
    
    def estimate_cost(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for a model call."""
        return self.pricing_manager.calculate_cost(model_name, input_tokens, output_tokens)
    
    def check_cost_limit(self, user_id: str, limit: float) -> dict:
        """Check if user has exceeded cost limit."""
        current_cost = self.get_user_cost(user_id)
        return {
            "can_execute": current_cost < limit,
            "current_cost": current_cost,
            "limit": limit,
            "remaining": limit - current_cost
        }
    
    def is_in_whitelist(self, user_id: str) -> bool:
        """Check if user is in whitelist."""
        return self.session.query(Whitelist).filter_by(user_id=user_id).first() is not None
    
    def check_usage(self, user_id: str, input_tokens: int, output_tokens: int, 
                   usage_metadata: Dict[str, Any] = None) -> dict:
        """Check usage limits."""
        # Use total_tokens from usage_metadata if available
        if usage_metadata and "total_tokens" in usage_metadata:
            total_tokens = usage_metadata["total_tokens"]
        else:
            total_tokens = input_tokens + output_tokens
        
        current_usage = self._get_sum_of_tokens_since_last_reset(user_id)
        remaining_tokens = self.max_daily_token - current_usage
        
        return {
            "can_execute": total_tokens <= remaining_tokens,
            "token-left": remaining_tokens,
            "current_usage": current_usage,
            "requested_tokens": total_tokens
        }
    
    def get_usage_metadata_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed usage statistics from usage metadata."""
        from sherpa_ai.cost_tracking.reporting import CostReporter
        reporter = CostReporter(self)
        return reporter.get_usage_metadata_statistics(user_id)
