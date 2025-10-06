"""Logging utilities for cost tracking with cost threshold alerts."""

from typing import Dict, Any, Optional, Callable
from loguru import logger
import sherpa_ai.config as cfg


class UsageLogger:
    """Usage logger with cost threshold alerts."""
    
    def __init__(
        self, 
        log_to_file: bool = False, 
        log_file_path: Optional[str] = None,
        daily_cost_limit: float = None,
        alert_threshold: float = None,
        alert_callback: Optional[Callable] = None
    ):
        """Initialize the usage logger with cost threshold monitoring."""
        self.log_to_file = log_to_file if log_to_file is not None else cfg.USAGE_LOG_TO_FILE
        self.log_file_path = log_file_path or cfg.USAGE_LOG_FILE_PATH
        self.daily_cost_limit = daily_cost_limit or cfg.DAILY_COST_LIMIT
        self.alert_threshold = alert_threshold or cfg.COST_ALERT_THRESHOLD
        self.alert_callback = alert_callback
        
        # Track user costs for threshold monitoring
        self.user_costs: Dict[str, float] = {}
        self.alerted_users: Dict[str, bool] = {}  # Track if user has been alerted
        
        if self.log_to_file:
            logger.add(self.log_file_path, rotation="10 MB", compression="zip", level="INFO")
    
    def log_usage(
        self,
        user_id: str,
        cost: float,
        model_name: str,
        session_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        usage_metadata: Optional[Dict[str, Any]] = None
    ):
        """Log usage data and check cost thresholds."""
        # Update user cost tracking
        self.user_costs[user_id] = self.user_costs.get(user_id, 0.0) + cost
        
        # Check cost thresholds and send alerts
        self._check_cost_thresholds(user_id, self.user_costs[user_id])
        
        # Log usage data if enabled
        if not self.log_to_file:
            return

        total_tokens = usage_metadata.get("total_tokens", 0) if usage_metadata else 0
        log_message = f"Usage: user_id={user_id}, tokens={total_tokens}, cost=${cost:.4f}, model={model_name}"
        
        if session_id:
            log_message += f", session_id={session_id}"
        if agent_name:
            log_message += f", agent_name={agent_name}"
        
        if usage_metadata:
            input_tokens = usage_metadata.get("input_tokens", 0)
            output_tokens = usage_metadata.get("output_tokens", 0)
            log_message += f", input_tokens={input_tokens}, output_tokens={output_tokens}"
            
            # Add detailed token info if available
            input_details = usage_metadata.get("input_token_details", {})
            output_details = usage_metadata.get("output_token_details", {})
            
            if output_details.get("reasoning", 0) > 0:
                log_message += f", reasoning_tokens={output_details['reasoning']}"
            if input_details.get("cache_creation", 0) > 0:
                log_message += f", cache_creation={input_details['cache_creation']}"
            if input_details.get("cache_read", 0) > 0:
                log_message += f", cache_read={input_details['cache_read']}"
        
        logger.info(log_message)
    
    def _check_cost_thresholds(self, user_id: str, total_cost: float):
        """Check cost thresholds and send alerts if needed."""
        # Calculate percentage of daily limit
        cost_percentage = (total_cost / self.daily_cost_limit) * 100
        
        # Check 80% threshold (warning)
        if cost_percentage >= 80 and not self.alerted_users.get(f"{user_id}_80", False):
            self._send_alert(user_id, total_cost, cost_percentage, "WARNING", 80)
            self.alerted_users[f"{user_id}_80"] = True
        
        # Check 100% threshold (critical)
        if cost_percentage >= 100 and not self.alerted_users.get(f"{user_id}_100", False):
            self._send_alert(user_id, total_cost, cost_percentage, "CRITICAL", 100)
            self.alerted_users[f"{user_id}_100"] = True
    
    def _send_alert(self, user_id: str, total_cost: float, cost_percentage: float, alert_level: str, threshold: int):
        """Send cost threshold alert."""
        alert_message = (
            f"🚨 {alert_level} ALERT: User {user_id} has reached {cost_percentage:.1f}% "
            f"of daily cost limit (${total_cost:.2f}/${self.daily_cost_limit:.2f})"
        )
        
        # Log the alert
        logger.warning(alert_message)
        
        # Call custom alert callback if provided
        if self.alert_callback:
            try:
                self.alert_callback(
                    user_id=user_id,
                    total_cost=total_cost,
                    cost_percentage=cost_percentage,
                    alert_level=alert_level,
                    threshold=threshold,
                    daily_limit=self.daily_cost_limit
                )
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    def get_user_cost(self, user_id: str) -> float:
        """Get current cost for a user."""
        return self.user_costs.get(user_id, 0.0)
    
    def reset_user_cost(self, user_id: str):
        """Reset cost tracking for a user (e.g., at start of new day)."""
        self.user_costs[user_id] = 0.0
        self.alerted_users[f"{user_id}_80"] = False
        self.alerted_users[f"{user_id}_100"] = False
    
    def reset_all_costs(self):
        """Reset cost tracking for all users."""
        self.user_costs.clear()
        self.alerted_users.clear()
    
