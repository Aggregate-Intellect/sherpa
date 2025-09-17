"""User usage tracking module for Sherpa AI.

This module provides functionality for tracking and managing user token usage,
including whitelisting users and enforcing daily token limits.

Example:
    >>> from sherpa_ai.database.user_usage_tracker import UserUsageTracker
    >>> tracker = UserUsageTracker()
    >>> tracker.check_usage("user123", 100)
    {'token-left': 900, 'can_execute': True, 'message': '', 'time_left': '23 hours : 59 min : 59 sec'}
"""

import time
from typing import Optional, Dict, Any

from loguru import logger
from sqlalchemy import Boolean, Column, Integer, String, Float, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import declarative_base, sessionmaker

import sherpa_ai.config as cfg
from sherpa_ai.verbose_loggers.base import BaseVerboseLogger
from sherpa_ai.verbose_loggers.verbose_loggers import DummyVerboseLogger


Base = declarative_base()


# Import the configurable pricing system
from sherpa_ai.cost_tracking.pricing import PricingManager


class UsageTracker(Base):
    """SQLAlchemy model for tracking LLM token usage on a per-user basis.

    This class represents the database table that stores token usage information
    for each user, including timestamps, reset flags, and cost information.

    Attributes:
        id (int): Primary key, auto-incrementing.
        user_id (str): ID of the user.
        token (int): Number of tokens used.
        cost (float): Cost in USD for this usage.
        model_name (str): Name of the model used.
        session_id (str): ID of the session.
        agent_name (str): Name of the agent.
        timestamp (int): Unix timestamp of the usage.
        reset_timestamp (bool): Whether this entry represents a usage reset.
        reminded_timestamp (bool): Whether the user has been reminded about usage limits.

    Example:
        >>> from sherpa_ai.database.user_usage_tracker import UsageTracker
        >>> usage = UsageTracker(user_id="user123", token=100, cost=0.002, timestamp=1234567890)
        >>> print(usage.user_id)
        user123
    """

    __tablename__ = "usage_tracker"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String)
    token = Column(Integer)
    cost = Column(Float, default=0.0)
    model_name = Column(String, default="unknown")
    session_id = Column(String, default=None)
    agent_name = Column(String, default=None)
    timestamp = Column(Integer)
    reset_timestamp = Column(Boolean)
    reminded_timestamp = Column(Boolean)


class Whitelist(Base):
    """Represents a trusted list of users whose usage is not tracked.

    This class represents the database table that stores whitelisted user IDs.
    Whitelisted users are not subject to token usage limits.

    Attributes:
        id (int): Primary key, auto-incrementing.
        user_id (str): Unique ID of the whitelisted user.

    Example:
        >>> from sherpa_ai.database.user_usage_tracker import Whitelist
        >>> whitelist = Whitelist(user_id="trusted_user123")
        >>> print(whitelist.user_id)
        trusted_user123
    """

    __tablename__ = "whitelist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, unique=True)


class UserUsageTracker:
    """Enables tracking of LLM token usage on a per-user basis.

    This class provides functionality to track, manage, and enforce token usage limits
    for users. It supports whitelisting users, tracking usage over time periods,
    and providing usage statistics.

    Attributes:
        db_name (str): Name of the database.
        db_url (str): URL for database connection.
        engine: SQLAlchemy engine instance.
        session: SQLAlchemy session instance.
        max_daily_token (int): Maximum daily token limit per user.
        verbose_logger: Logger for verbose output.
        is_reminded (bool): Whether the user has been reminded about usage limits.
        usage_percentage_allowed (int): Percentage of limit at which to remind users.
        limit_time_size_in_hours (float): Time window for usage limits in hours.
        bucket_name (str): S3 bucket name for database backup.
        s3_file_key (str): S3 key for database backup file.
        local_file_path (str): Local path for database file.

    Example:
        >>> from sherpa_ai.database.user_usage_tracker import UserUsageTracker
        >>> tracker = UserUsageTracker()
        >>> result = tracker.check_usage("user123", 100)
        >>> print(result["token-left"])
        900
    """

    def __init__(
        self,
        db_name=cfg.DB_NAME,
        db_url=cfg.DB_URL,
        s3_file_key="token_counter.db",
        bucket_name="sherpa-sqlight",
        verbose_logger: BaseVerboseLogger = DummyVerboseLogger(),
        engine=None,
        session=None,
        pricing_manager: Optional[PricingManager] = None,
    ):
        """Initialize the UserUsageTracker.

        Args:
            db_name (str, optional): Name of the database. Defaults to cfg.DB_NAME.
            db_url (str, optional): URL for database connection. Defaults to cfg.DB_URL.
            s3_file_key (str, optional): S3 key for database backup. Defaults to "token_counter.db".
            bucket_name (str, optional): S3 bucket name. Defaults to "sherpa-sqlight".
            verbose_logger (BaseVerboseLogger, optional): Logger for verbose output. Defaults to DummyVerboseLogger().
            engine (optional): SQLAlchemy engine instance. Defaults to None.
            session (optional): SQLAlchemy session instance. Defaults to None.
            pricing_manager (PricingManager, optional): Pricing manager instance. Defaults to None (creates new one).

        Raises:
            ImportError: If boto3 package is not installed.

        Example:
            >>> from sherpa_ai.database.user_usage_tracker import UserUsageTracker
            >>> tracker = UserUsageTracker(db_name="my_db", db_url="sqlite:///my_db.db")
            >>> print(tracker.db_name)
            my_db
        """
        try:
            import boto3
            UserUsageTracker.boto3 = boto3
        except ImportError:
            raise ImportError(
                "Could not import boto3 python package."
                "This is needed in order to use the UserUsageTracker."
                "Please install boto3 with 'pip install boto3'."
            )

        self.db_name = db_name
        self.db_url = db_url
        self.engine = engine or create_engine(self.db_url)
        if session:
            self.session = session
        else:
            Session = sessionmaker(bind=self.engine)
            self.session = Session()

        self.create_table()
        self.max_daily_token = cfg.DAILY_TOKEN_LIMIT
        self.verbose_logger = verbose_logger
        self.is_reminded = False
        self.usage_percentage_allowed = 75
        self.limit_time_size_in_hours = float(cfg.LIMIT_TIME_SIZE_IN_HOURS or 24)
        self.bucket_name = bucket_name
        self.s3_file_key = s3_file_key
        self.local_file_path = f"./{self.db_name}"
        
        # Initialize pricing manager
        self.pricing_manager = pricing_manager or PricingManager()

    @classmethod
    def download_from_s3(
        cls,
        db_name=cfg.DB_NAME,
        db_url=cfg.DB_URL,
        s3_file_key="token_counter.db",
        bucket_name="sherpa-sqlight",
        verbose_logger: BaseVerboseLogger = DummyVerboseLogger(),
    ):
        """Download usage tracking database from Amazon S3 to local file.

        This method downloads the database file from S3 and creates a new UserUsageTracker
        instance with the downloaded database.

        Args:
            db_name (str, optional): Name of the database. Defaults to cfg.DB_NAME.
            db_url (str, optional): URL for database connection. Defaults to cfg.DB_URL.
            s3_file_key (str, optional): S3 key for database backup. Defaults to "token_counter.db".
            bucket_name (str, optional): S3 bucket name. Defaults to "sherpa-sqlight".
            verbose_logger (BaseVerboseLogger, optional): Logger for verbose output. Defaults to DummyVerboseLogger().

        Returns:
            UserUsageTracker: A new UserUsageTracker instance with the downloaded database.

        Example:
            >>> from sherpa_ai.database.user_usage_tracker import UserUsageTracker
            >>> tracker = UserUsageTracker.download_from_s3(bucket_name="my-bucket")
            >>> print(tracker.db_name)
            token_counter
        """
        local_file_path = f"./{db_name}"
        s3 = cls.boto3.client("s3")
        try:
            s3.download_file(bucket_name, s3_file_key, local_file_path)
        except Exception as e:
            logger.error(f"Error download from s3: {str(e)}")
        return cls(
            db_name=db_name,
            db_url=db_url,
            s3_file_key=s3_file_key,
            bucket_name=bucket_name,
            verbose_logger=verbose_logger,
        )

    def upload_to_s3(self):
        """Upload usage tracking database file to Amazon S3.

        This method uploads the local database file to the specified S3 bucket.

        Example:
            >>> from sherpa_ai.database.user_usage_tracker import UserUsageTracker
            >>> tracker = UserUsageTracker()
            >>> tracker.upload_to_s3()  # Uploads the database to S3
        """
        s3 = UserUsageTracker.boto3.client("s3")
        try:
            s3.upload_file(self.local_file_path, self.bucket_name, self.s3_file_key)
        except Exception as e:
            logger.error(f"Error uploading file to S3: {str(e)}")

    def create_table(self):
        """Create the necessary tables in the database.

        This method creates the UsageTracker and Whitelist tables if they don't exist.

        Example:
            >>> from sherpa_ai.database.user_usage_tracker import UserUsageTracker
            >>> tracker = UserUsageTracker()
            >>> tracker.create_table()  # Creates the tables in the database
        """
        Base.metadata.create_all(self.engine)

    def add_to_whitelist(self, user_id):
        """Add a user to the whitelist.

        This method adds a user ID to the whitelist table. Whitelisted users are not
        subject to token usage limits.

        Args:
            user_id (str): ID of the user to be added to the whitelist.

        Example:
            >>> from sherpa_ai.database.user_usage_tracker import UserUsageTracker
            >>> tracker = UserUsageTracker()
            >>> tracker.add_to_whitelist("trusted_user123")
        """
        user = Whitelist(user_id=user_id)
        try:
            self.session.add(user)
            self.session.commit()
        except IntegrityError:
            logger.warning(f"Ignoring user ID {user_id}, already whitelisted")
            self.session.rollback()

        if not cfg.FLASK_DEBUG:
            self.upload_to_s3()

    def get_all_whitelisted_ids(self):
        """Get a list of all whitelisted user IDs.

        Returns:
            list: List of whitelisted user IDs.

        Example:
            >>> from sherpa_ai.database.user_usage_tracker import UserUsageTracker
            >>> tracker = UserUsageTracker()
            >>> whitelisted_ids = tracker.get_all_whitelisted_ids()
            >>> print(whitelisted_ids)
            ['user1', 'user2', 'user3']
        """
        whitelisted_ids = [user.user_id for user in self.session.query(Whitelist).all()]
        return whitelisted_ids

    def get_whitelist_by_user_id(self, user_id):
        """Get whitelist information for a specific user.

        Args:
            user_id (str): ID of the user to look up.

        Returns:
            list: List of dictionaries containing whitelist information for the user.

        Example:
            >>> from sherpa_ai.database.user_usage_tracker import UserUsageTracker
            >>> tracker = UserUsageTracker()
            >>> whitelist_info = tracker.get_whitelist_by_user_id("user123")
            >>> print(whitelist_info)
            [{'id': 1, 'user_id': 'user123'}]
        """
        data = self.session.query(Whitelist).filter_by(user_id=user_id).all()
        return [{"id": item.id, "user_id": item.user_id} for item in data]

    def is_in_whitelist(self, user_id):
        """Check if a user is in the whitelist.

        Args:
            user_id (str): ID of the user to check.

        Returns:
            bool: True if the user is whitelisted, False otherwise.

        Example:
            >>> from sherpa_ai.database.user_usage_tracker import UserUsageTracker
            >>> tracker = UserUsageTracker()
            >>> is_whitelisted = tracker.is_in_whitelist("user123")
            >>> print(is_whitelisted)
            False
        """
        return bool(self.get_whitelist_by_user_id(user_id))

    def add_and_check_data(
        self, user_id, token, reset_timestamp=False, reminded_timestamp=False
    ):
        """Add usage data and check for usage limits.

        This method adds usage data for a user and checks if they need to be
        reminded about their usage limits.

        Args:
            user_id (str): ID of the user.
            token (int): Number of tokens used.
            reset_timestamp (bool, optional): Whether to reset the timestamp. Defaults to False.
            reminded_timestamp (bool, optional): Whether to mark as reminded. Defaults to False.

        Example:
            >>> from sherpa_ai.database.user_usage_tracker import UserUsageTracker
            >>> tracker = UserUsageTracker()
            >>> tracker.add_and_check_data("user123", 100)
        """
        self.add_data(
            user_id=user_id,
            token=token,
            reset_timestamp=reset_timestamp,
            reminded_timestamp=reminded_timestamp,
        )
        self.remind_user_of_daily_token_limit(user_id=user_id)

    def add_data(
        self, 
        user_id, 
        token, 
        reset_timestamp=False, 
        reminded_timestamp=False,
        cost: Optional[float] = None,
        model_name: Optional[str] = None,
        session_id: Optional[str] = None,
        agent_name: Optional[str] = None
    ):
        """Add usage data for a user.

        Args:
            user_id (str): ID of the user.
            token (int): Number of tokens used.
            reset_timestamp (bool, optional): Whether to reset the timestamp. Defaults to False.
            reminded_timestamp (bool, optional): Whether to mark as reminded. Defaults to False.
            cost (float, optional): Cost in USD. If None, will be calculated from model_name and tokens.
            model_name (str, optional): Name of the model used.
            session_id (str, optional): ID of the session.
            agent_name (str, optional): Name of the agent.

        Example:
            >>> from sherpa_ai.database.user_usage_tracker import UserUsageTracker
            >>> tracker = UserUsageTracker()
            >>> tracker.add_data("user123", 100, model_name="gpt-4o-mini")
        """
        # Calculate cost if not provided
        if cost is None and model_name:
            cost = self.pricing_manager.calculate_cost(model_name, token)
        elif cost is None:
            cost = 0.0
        
        data = UsageTracker(
            user_id=user_id,
            token=token,
            cost=cost,
            model_name=model_name or "unknown",
            session_id=session_id,
            agent_name=agent_name,
            timestamp=int(time.time()),
            reset_timestamp=reset_timestamp,
            reminded_timestamp=reminded_timestamp,
        )
        self.session.add(data)
        self.session.commit()
        self.upload_to_s3()

    def percentage_used(self, user_id):
        """Calculate the percentage of daily token limit used by a user.

        Args:
            user_id (str): ID of the user.

        Returns:
            float: Percentage of daily token limit used.

        Example:
            >>> from sherpa_ai.database.user_usage_tracker import UserUsageTracker
            >>> tracker = UserUsageTracker()
            >>> percentage = tracker.percentage_used("user123")
            >>> print(f"{percentage}% of daily limit used")
            10.0% of daily limit used
        """
        total_token_since_last_reset = self.get_sum_of_tokens_since_last_reset(
            user_id=user_id
        )
        return (total_token_since_last_reset * 100) / self.max_daily_token

    def remind_user_of_daily_token_limit(self, user_id):
        """Remind user when they approach their daily token limit.

        This method checks if a user has used more than the allowed percentage of their
        daily token limit and sends a reminder if needed.

        Args:
            user_id (str): ID of the user to check.

        Example:
            >>> from sherpa_ai.database.user_usage_tracker import UserUsageTracker
            >>> tracker = UserUsageTracker()
            >>> tracker.remind_user_of_daily_token_limit("user123")
        """
        user_is_whitelisted = self.is_in_whitelist(user_id)
        self.is_reminded = self.check_if_reminded(user_id=user_id)
        if not user_is_whitelisted and not self.is_reminded:
            if (
                self.percentage_used(user_id=user_id) > self.usage_percentage_allowed
                and not self.is_reminded
            ):
                self.add_data(user_id=user_id, token=0, reminded_timestamp=True)
                self.verbose_logger.log(
                    f"Hi friend, you have used up {self.usage_percentage_allowed}% of your daily token limit. once you go over the limit there will be a 24 hour cool down period after which you can continue using Sherpa! be awesome!"
                )

    def get_data_since_last_reset(self, user_id):
        """Get usage data since the last reset for a user.

        Args:
            user_id (str): ID of the user.

        Returns:
            list: List of dictionaries containing usage data since last reset.

        Example:
            >>> from sherpa_ai.database.user_usage_tracker import UserUsageTracker
            >>> tracker = UserUsageTracker()
            >>> data = tracker.get_data_since_last_reset("user123")
            >>> print(data)
            [{'id': 1, 'user_id': 'user123', 'token': 100, 'timestamp': 1234567890, 'reset_timestamp': False, 'reminded_timestamp': False}]
        """
        last_reset_info = self.get_last_reset_info(user_id)
        # if there is no reset point before all the users interaction will be taken as a data since last reset
        if last_reset_info is None or last_reset_info["id"] is None:
            data = self.session.query(UsageTracker).filter_by(user_id=user_id).all()
            return [
                {
                    "id": item.id,
                    "user_id": item.user_id,
                    "token": item.token,
                    "cost": item.cost,
                    "model_name": item.model_name,
                    "session_id": item.session_id,
                    "agent_name": item.agent_name,
                    "timestamp": item.timestamp,
                    "reset_timestamp": item.reset_timestamp,
                    "reminded_timestamp": item.reminded_timestamp,
                }
                for item in data
            ]
        # return every thing from the last reset point.
        # since id is incremental everything greater than the earliest reset point
        data = (
            self.session.query(UsageTracker)
            .filter(
                UsageTracker.user_id == user_id,
                UsageTracker.id >= last_reset_info["id"],
            )
            .all()
        )

        return [
            {
                "id": item.id,
                "user_id": item.user_id,
                "token": item.token,
                "cost": item.cost,
                "model_name": item.model_name,
                "session_id": item.session_id,
                "agent_name": item.agent_name,
                "timestamp": item.timestamp,
                "reset_timestamp": item.reset_timestamp,
                "reminded_timestamp": item.reminded_timestamp,
            }
            for item in data
        ]

    def check_if_reminded(self, user_id):
        """Check if a user has been reminded about their usage limits.

        Args:
            user_id (str): ID of the user to check.

        Returns:
            bool: True if the user has been reminded, False otherwise.

        Example:
            >>> from sherpa_ai.database.user_usage_tracker import UserUsageTracker
            >>> tracker = UserUsageTracker()
            >>> is_reminded = tracker.check_if_reminded("user123")
            >>> print(is_reminded)
            False
        """
        data_list = self.get_data_since_last_reset(user_id)
        is_reminded_true = any(
            item.get("reminded_timestamp", False) for item in data_list
        )

        return is_reminded_true

    def get_sum_of_tokens_since_last_reset(self, user_id):
        """Calculate total tokens used since last reset for a user.

        Args:
            user_id (str): ID of the user.

        Returns:
            int: Total number of tokens used since last reset.

        Example:
            >>> from sherpa_ai.database.user_usage_tracker import UserUsageTracker
            >>> tracker = UserUsageTracker()
            >>> total_tokens = tracker.get_sum_of_tokens_since_last_reset("user123")
            >>> print(f"Total tokens used: {total_tokens}")
            Total tokens used: 500
        """
        data_since_last_reset = self.get_data_since_last_reset(user_id)

        if len(data_since_last_reset) == 1 and "user_id" in data_since_last_reset[0]:
            return data_since_last_reset[0]["token"]

        token_sum = sum(item["token"] for item in data_since_last_reset)
        return token_sum

    def reset_usage(self, user_id, token_amount):
        """Reset usage data for a user.

        Args:
            user_id (str): ID of the user.
            token_amount (int): Number of tokens to reset.

        Example:
            >>> from sherpa_ai.database.user_usage_tracker import UserUsageTracker
            >>> tracker = UserUsageTracker()
            >>> tracker.reset_usage("user123", 0)
        """
        self.add_and_check_data(
            user_id=user_id, token=token_amount, reset_timestamp=True
        )

    def get_last_reset_info(self, user_id):
        """Get information about the last usage reset for a user.

        Args:
            user_id (str): ID of the user.

        Returns:
            dict or None: Dictionary containing last reset information or None if no reset found.

        Example:
            >>> from sherpa_ai.database.user_usage_tracker import UserUsageTracker
            >>> tracker = UserUsageTracker()
            >>> reset_info = tracker.get_last_reset_info("user123")
            >>> if reset_info:
            ...     print(f"Last reset at timestamp: {reset_info['timestamp']}")
            Last reset at timestamp: 1234567890
        """
        data = (
            self.session.query(UsageTracker.id, UsageTracker.timestamp)
            .filter(UsageTracker.user_id == user_id, UsageTracker.reset_timestamp == 1)
            .order_by(UsageTracker.timestamp.desc())
            .first()
        )

        if data:
            last_reset_id, last_reset_timestamp = data
            return {"id": last_reset_id, "timestamp": last_reset_timestamp}
        else:
            return None

    def seconds_to_hms(self, seconds):
        """Convert seconds to hours, minutes, and seconds format.

        Args:
            seconds (int): Number of seconds to convert.

        Returns:
            str: Formatted string in "hours : minutes : seconds" format.

        Example:
            >>> from sherpa_ai.database.user_usage_tracker import UserUsageTracker
            >>> tracker = UserUsageTracker()
            >>> time_str = tracker.seconds_to_hms(3665)
            >>> print(time_str)
            23 hours : 0 min : 55 sec
        """
        remaining_seconds = int(float(self.limit_time_size_in_hours) * 3600 - seconds)
        hours = remaining_seconds // 3600
        minutes = (remaining_seconds % 3600) // 60
        seconds = remaining_seconds % 60

        return f"{hours} hours : {minutes} min : {seconds} sec"

    def check_usage(self, user_id, token_amount):
        """Check if a user can consume more tokens.

        This method checks if a user has exceeded their daily token limit and
        determines if they can consume more tokens.

        Args:
            user_id (str): ID of the user.
            token_amount (int): Number of tokens to check.

        Returns:
            dict: Dictionary containing usage information including:
                - token-left: Remaining tokens
                - can_execute: Whether the user can consume more tokens
                - message: Any relevant message about usage limits
                - time_left: Time remaining until next reset

        Example:
            >>> from sherpa_ai.database.user_usage_tracker import UserUsageTracker
            >>> tracker = UserUsageTracker()
            >>> result = tracker.check_usage("user123", 100)
            >>> print(f"Can execute: {result['can_execute']}, Tokens left: {result['token-left']}")
            Can execute: True, Tokens left: 900
        """
        user_is_whitelisted = self.is_in_whitelist(user_id)
        if user_is_whitelisted:
            return {
                "token-left": self.max_daily_token,
                "can_execute": True,
                "message": "",
                "time_left": "",
            }
        else:
            last_reset_info = self.get_last_reset_info(user_id=user_id)
            #
            time_since_last_reset = None

            if last_reset_info is not None and last_reset_info["timestamp"] is not None:
                time_since_last_reset = int(time.time()) - last_reset_info["timestamp"]

            if int(token_amount) > self.max_daily_token:
                return {
                    "token-left": 0,
                    "can_execute": False,
                    "message": "your request exceeds token limit. try using smaller context.",
                    "time_left": "",
                }

            if time_since_last_reset is None or (
                time_since_last_reset != 0
                and time_since_last_reset > 3600 * float(self.limit_time_size_in_hours)
            ):
                self.reset_usage(user_id=user_id, token_amount=token_amount)
                return {
                    "token-left": self.max_daily_token,
                    "can_execute": True,
                    "message": "",
                    "time_left": "",
                }
            else:
                total_token_since_last_reset = self.get_sum_of_tokens_since_last_reset(
                    user_id=user_id
                )

                remaining_tokens = self.max_daily_token - total_token_since_last_reset
                if remaining_tokens <= 0:
                    return {
                        "token-left": remaining_tokens,
                        "can_execute": False,
                        "message": "daily usage limit exceeded. you can try after 24 hours",
                        "time_left": self.seconds_to_hms(time_since_last_reset),
                    }
                else:
                    self.add_and_check_data(user_id=user_id, token=token_amount)
                    return {
                        "token-left": remaining_tokens,
                        "current_token": token_amount,
                        "can_execute": True,
                        "message": "",
                        "time_left": self.seconds_to_hms(time_since_last_reset),
                    }

    def get_all_data(self):
        """Get all usage tracking data.

        Returns:
            list: List of all UsageTracker records.

        Example:
            >>> from sherpa_ai.database.user_usage_tracker import UserUsageTracker
            >>> tracker = UserUsageTracker()
            >>> all_data = tracker.get_all_data()
            >>> print(f"Total records: {len(all_data)}")
            Total records: 42
        """
        data = self.session.query(UsageTracker).all()
        return [item for item in data]

    def get_user_cost(self, user_id: str) -> float:
        """Get total cost for a user since last reset.

        Args:
            user_id (str): ID of the user.

        Returns:
            float: Total cost in USD.

        Example:
            >>> from sherpa_ai.database.user_usage_tracker import UserUsageTracker
            >>> tracker = UserUsageTracker()
            >>> cost = tracker.get_user_cost("user123")
            >>> print(f"Total cost: ${cost:.4f}")
            Total cost: $2.3456
        """
        # For simplicity, get all data for the user (can be enhanced later with reset logic)
        data = self.session.query(UsageTracker).filter_by(user_id=user_id).all()
        return sum(item.cost for item in data)

    def get_session_cost(self, session_id: str) -> float:
        """Get total cost for a session.

        Args:
            session_id (str): ID of the session.

        Returns:
            float: Total cost in USD.

        Example:
            >>> from sherpa_ai.database.user_usage_tracker import UserUsageTracker
            >>> tracker = UserUsageTracker()
            >>> cost = tracker.get_session_cost("session456")
            >>> print(f"Session cost: ${cost:.4f}")
            Session cost: $1.2345
        """
        data = self.session.query(UsageTracker).filter_by(session_id=session_id).all()
        return sum(item.cost for item in data)

    def get_agent_cost(self, agent_name: str) -> float:
        """Get total cost for an agent.

        Args:
            agent_name (str): Name of the agent.

        Returns:
            float: Total cost in USD.

        Example:
            >>> from sherpa_ai.database.user_usage_tracker import UserUsageTracker
            >>> tracker = UserUsageTracker()
            >>> cost = tracker.get_agent_cost("QA Agent")
            >>> print(f"Agent cost: ${cost:.4f}")
            Agent cost: $3.4567
        """
        data = self.session.query(UsageTracker).filter_by(agent_name=agent_name).all()
        return sum(item.cost for item in data)

    def get_cost_summary(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get cost summary for a user or all users.

        Args:
            user_id (str, optional): ID of the user. If None, returns summary for all users.

        Returns:
            Dict containing cost summary information.

        Example:
            >>> from sherpa_ai.database.user_usage_tracker import UserUsageTracker
            >>> tracker = UserUsageTracker()
            >>> summary = tracker.get_cost_summary("user123")
            >>> print(f"Total cost: ${summary['total_cost']:.4f}")
            Total cost: $5.6789
        """
        if user_id:
            data = self.session.query(UsageTracker).filter_by(user_id=user_id).all()
            total_cost = sum(item.cost for item in data)
            total_tokens = sum(item.token for item in data)
            total_calls = len(data)
        else:
            data = self.session.query(UsageTracker).all()
            total_cost = sum(item.cost for item in data)
            total_tokens = sum(item.token for item in data)
            total_calls = len(data)

        # Get breakdown by model
        model_breakdown = {}
        for item in data:
            model = item.get("model_name", "unknown") if isinstance(item, dict) else item.model_name
            cost = item.get("cost", 0) if isinstance(item, dict) else item.cost
            model_breakdown[model] = model_breakdown.get(model, 0) + cost

        return {
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "total_calls": total_calls,
            "model_breakdown": model_breakdown,
            "average_cost_per_call": total_cost / total_calls if total_calls > 0 else 0
        }

    def estimate_cost(self, model_name: str, estimated_tokens: int) -> float:
        """Estimate cost for a potential LLM call.

        Args:
            model_name (str): Name of the model.
            estimated_tokens (int): Estimated number of tokens.

        Returns:
            float: Estimated cost in USD.

        Example:
            >>> from sherpa_ai.database.user_usage_tracker import UserUsageTracker
            >>> tracker = UserUsageTracker()
            >>> cost = tracker.estimate_cost("gpt-4o-mini", 1000)
            >>> print(f"Estimated cost: ${cost:.4f}")
            Estimated cost: $0.3750
        """
        return self.pricing_manager.calculate_cost(model_name, estimated_tokens)

    def check_cost_limit(self, user_id: str, estimated_cost: float = 0.0) -> Dict[str, Any]:
        """Check if user is approaching or has exceeded cost limits.
        
        Args:
            user_id: ID of the user.
            estimated_cost: Estimated cost for the upcoming call.
            
        Returns:
            Dictionary with cost limit information.
        """
        import sherpa_ai.config as cfg
        
        current_cost = self.get_user_cost(user_id)
        total_cost = current_cost + estimated_cost
        daily_limit = cfg.DAILY_COST_LIMIT
        alert_threshold = cfg.COST_ALERT_THRESHOLD
        
        can_execute = total_cost <= daily_limit
        alert_threshold_cost = daily_limit * alert_threshold
        
        return {
            "current_cost": current_cost,
            "estimated_cost": estimated_cost,
            "total_cost": total_cost,
            "daily_limit": daily_limit,
            "can_execute": can_execute,
            "alert_threshold": alert_threshold_cost,
            "approaching_limit": total_cost >= alert_threshold_cost,
            "message": "" if can_execute else f"Daily cost limit of ${daily_limit:.2f} exceeded"
        }

    def close_connection(self):
        """Close the database connection.

        This method should be called when the UserUsageTracker is no longer needed
        to properly close the database connection.

        Example:
            >>> from sherpa_ai.database.user_usage_tracker import UserUsageTracker
            >>> tracker = UserUsageTracker()
            >>> tracker.close_connection()  # Closes the database connection
        """
        self.session.close()
