import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sherpa_ai.config as cfg
from sherpa_ai.database.user_usage_tracker import (
    UsageTracker,
    UserUsageTracker,
    Whitelist,
)
from sherpa_ai.verbose_loggers.base import BaseVerboseLogger


USER_ID = "test_id"
TEST_DB_NAME = "test_usage.db"
TEST_DB_URL = "sqlite:///test_usage.db"

engine = create_engine(TEST_DB_URL)
Session = sessionmaker()


@pytest.fixture(scope="module")
def connection():
    """Returns a connection to the test database"""
    connection = engine.connect()
    yield connection
    connection.close()


@pytest.fixture(scope="function")
def session(connection):
    """
    Returns a database session that wraps test activities in a transaction
    which rolls back after the test returns
    """
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()


def delete_table_data(db):
    db.session.query(Whitelist).delete()
    db.session.query(UsageTracker).delete()
    db.session.commit()


@pytest.fixture(scope="function")
def tracker(session):
    """
    Returns a UserUsageTracker instance using the test database and
    session, deleting table rows before yielding to the test
    so that we start with empty tables
    """
    db = UserUsageTracker(
        db_name=TEST_DB_NAME, db_url=TEST_DB_URL, engine=engine, session=session
    )
    # Create tables with new schema
    db.create_table()
    delete_table_data(db)
    yield db


@pytest.fixture(scope="function")
def mock_s3_client(autouse=True):
    with patch("boto3.client") as mock_boto3:
        mock_s3 = MagicMock()
        mock_boto3.return_value = mock_s3
        yield mock_s3


def test_usage_tracker_time_limit_is_set_in_app_config():
    with patch("sherpa_ai.database.user_usage_tracker.cfg") as mock_config:
        mock_config.LIMIT_TIME_SIZE_IN_HOURS = "3.14159"
        db = UserUsageTracker(
            db_name=TEST_DB_NAME, db_url=TEST_DB_URL, engine=engine, session=session
        )
        assert db.limit_time_size_in_hours is not None
        assert isinstance(db.limit_time_size_in_hours, float)
        assert db.limit_time_size_in_hours == 3.14159


def test_usage_tracker_time_limit_defaults_to_24_hours():
    with patch("sherpa_ai.database.user_usage_tracker.cfg") as mock_config:
        mock_config.LIMIT_TIME_SIZE_IN_HOURS = None
        db = UserUsageTracker(db_name=TEST_DB_NAME, db_url=TEST_DB_URL)
        assert db.limit_time_size_in_hours == 24.0


def test_add_to_whitelist_adds_a_user_id(tracker):
    tracker.add_to_whitelist(user_id=USER_ID)
    assert USER_ID in tracker.get_all_whitelisted_ids()


def test_add_to_whitelist_ignores_duplicate_user_ids():
    db = UserUsageTracker(db_name=TEST_DB_NAME, db_url=TEST_DB_URL)
    delete_table_data((db))
    db.add_to_whitelist(user_id=USER_ID)
    assert len(db.get_all_whitelisted_ids()) == 1
    db.add_to_whitelist(user_id=USER_ID)
    assert len(db.get_all_whitelisted_ids()) == 1


def test_add_to_whitelist_uploads_to_s3_when_flask_debug_is_false(
    mock_s3_client, tracker
):
    with patch("sherpa_ai.database.user_usage_tracker.cfg") as mock_config:
        mock_config.FLASK_DEBUG = False
        tracker.add_to_whitelist(user_id=USER_ID)
        mock_s3_client.upload_file.assert_called()


def test_add_to_whitelist_does_not_upload_to_s3_when_flask_debug_is_true(
    mock_s3_client, tracker
):
    with patch("sherpa_ai.database.user_usage_tracker.cfg") as mock_config:
        mock_config.FLASK_DEBUG = True
        tracker.add_to_whitelist(user_id=USER_ID)
        mock_s3_client.upload_file.assert_not_called()


def test_get_whitelist_by_user_id(tracker, mock_s3_client):
    assert tracker.get_whitelist_by_user_id(USER_ID) == []
    tracker.add_to_whitelist(user_id=USER_ID)
    whitelisted_ids = tracker.get_whitelist_by_user_id(USER_ID)
    assert len(whitelisted_ids) == 1
    assert whitelisted_ids[0]["user_id"] == USER_ID


def test_is_in_whitelist(tracker, mock_s3_client):
    assert not tracker.is_in_whitelist(USER_ID)
    tracker.add_to_whitelist(user_id=USER_ID)
    assert tracker.is_in_whitelist(USER_ID)


def test_check_usage_limits_remaining_tokens(tracker, mock_s3_client):
    tracker.max_daily_token = 2000
    tracker.limit_time_size_in_hours = 0.1
    check_usage = tracker.check_usage(token_amount="3000", user_id="jack")  # nosec B106
    assert check_usage["can_execute"] is False
    check_usage = tracker.check_usage(token_amount="1000", user_id="jack")  # nosec B106
    assert (
        check_usage["can_execute"] is True and check_usage["token-left"] == 2000
    )  # nosec B106
    check_usage = tracker.check_usage(token_amount="1000", user_id="jack")  # nosec B106
    assert check_usage["can_execute"] is True and check_usage["token-left"] == 1000
    check_usage = tracker.check_usage(token_amount="1000", user_id="jack")  # nosec B106
    assert check_usage["can_execute"] is False and check_usage["token-left"] == 0


# # TODO mock time or remove this entirely
# def test_usage_reset_after_a_given_time(db_setup_teardown, mock_s3_client):
#     db = UserUsageTracker(db_name=TEST_DB_NAME, db_url=TEST_DB_URL)
#     db.max_daily_token = 2000
#     db.limit_time_size_in_hours = 0.001  # 3.6 seconds
#     db.check_usage(token_amount="2000", user_id="jack")
#     check_usage = db.check_usage(token_amount="10", user_id="jack")
#     assert check_usage["can_execute"] is False

#     # check if the usage tracker has been updated after 4 seconds
#     timer = threading.Timer(4.0, (lambda: ""))
#     timer.start()
#     timer.join()
#     check_usage = db.check_usage(token_amount="10", user_id="jack")
#     assert check_usage["can_execute"] is True


def test_download_from_s3_calls_download_file(mock_s3_client, tracker):
    tracker.download_from_s3()
    mock_s3_client.download_file.assert_called_with(
        "sherpa-sqlight", "token_counter.db", "./token_counter.db"
    )


def test_download_from_s3_returns_class_instance(mock_s3_client):
    ret = UserUsageTracker.download_from_s3(db_name=TEST_DB_NAME, db_url=TEST_DB_URL)
    assert isinstance(ret, UserUsageTracker)
    assert ret.db_name == TEST_DB_NAME
    assert ret.db_url == TEST_DB_URL
    assert ret.s3_file_key == "token_counter.db"
    assert ret.bucket_name == "sherpa-sqlight"
    assert isinstance(ret.verbose_logger, BaseVerboseLogger)


def test_upload_to_s3_calls_upload_file(mock_s3_client):
    db = UserUsageTracker(db_name=TEST_DB_NAME, db_url=TEST_DB_URL)
    db.upload_to_s3()
    mock_s3_client.upload_file.assert_called_with(
        db.local_file_path, db.bucket_name, db.s3_file_key
    )


def test_reminder_message_after_75_percent_usage(mock_s3_client):
    class TestLogger(BaseVerboseLogger):
        def __init__(self) -> None:
            self.message = ""

        def log(self, message):
            self.message = message

    logger = TestLogger()
    db = UserUsageTracker(
        db_name=TEST_DB_NAME,
        db_url=TEST_DB_URL,
        engine=engine,
        verbose_logger=logger,
    )
    delete_table_data(db)

    db.max_daily_token = 1000
    db.add_and_check_data(user_id="jack", token=751)
    assert (
        logger.message[0:9] == "Hi friend"
    ), "user should get a reminder message after 75% usage"


# Pricing and Cost Tracking Tests

def test_pricing_manager_integration():
    """Test that UserUsageTracker uses the pricing manager correctly."""
    from sherpa_ai.cost_tracking.pricing import PricingManager
    
    # Test with known model
    pricing = PricingManager()
    cost = pricing.calculate_cost("gpt-4o", 1000)
    assert cost == 0.01
    
    # Test with unknown model (should use default)
    cost = pricing.calculate_cost("unknown-model", 1000)
    assert cost == 0.002
    
    # Test with different token amounts
    cost = pricing.calculate_cost("gpt-4o", 500)
    assert cost == 0.005


def test_add_data_with_cost_calculation(tracker, mock_s3_client):
    """Test that add_data automatically calculates cost when model_name is provided."""
    # Add data with model name - cost should be automatically calculated
    tracker.add_data(
        user_id=USER_ID,
        token=1000,
        model_name="gpt-4o"
    )
    
    # Check that cost was calculated and stored
    data = tracker.get_data_since_last_reset(USER_ID)
    assert len(data) == 1
    assert data[0]["token"] == 1000
    assert data[0]["cost"] == 0.01  # gpt-4o pricing
    assert data[0]["model_name"] == "gpt-4o"


def test_add_data_with_explicit_cost(tracker, mock_s3_client):
    """Test that add_data uses explicit cost when provided."""
    # Add data with explicit cost
    tracker.add_data(
        user_id=USER_ID,
        token=1000,
        cost=0.05,  # Explicit cost
        model_name="gpt-4o"
    )
    
    # Check that explicit cost was used
    data = tracker.get_data_since_last_reset(USER_ID)
    assert len(data) == 1
    assert data[0]["cost"] == 0.05  # Explicit cost, not calculated


def test_add_data_without_cost_or_model(tracker, mock_s3_client):
    """Test that add_data defaults to zero cost when neither cost nor model_name provided."""
    # Add data without cost or model name
    tracker.add_data(
        user_id=USER_ID,
        token=1000
    )
    
    # Check that cost defaults to 0.0
    data = tracker.get_data_since_last_reset(USER_ID)
    assert len(data) == 1
    assert data[0]["cost"] == 0.0


def test_get_user_cost(tracker, mock_s3_client):
    """Test getting total cost for a user."""
    # Add multiple usage records
    tracker.add_data(user_id=USER_ID, token=1000, model_name="gpt-4o")  # $0.01
    tracker.add_data(user_id=USER_ID, token=500, model_name="gpt-4o-mini")  # $0.0001875
    
    total_cost = tracker.get_user_cost(USER_ID)
    expected_cost = 0.01 + 0.0001875
    assert abs(total_cost - expected_cost) < 0.000001


def test_get_session_cost(tracker, mock_s3_client):
    """Test getting total cost for a session."""
    session_id = "test_session"
    
    # Add multiple usage records for the same session
    tracker.add_data(
        user_id=USER_ID, 
        token=1000, 
        model_name="gpt-4o",
        session_id=session_id
    )
    tracker.add_data(
        user_id=USER_ID, 
        token=500, 
        model_name="gpt-4o-mini",
        session_id=session_id
    )
    
    total_cost = tracker.get_session_cost(session_id)
    expected_cost = 0.01 + 0.0001875
    assert abs(total_cost - expected_cost) < 0.000001


def test_get_agent_cost(tracker, mock_s3_client):
    """Test getting total cost for an agent."""
    agent_name = "test_agent"
    
    # Add multiple usage records for the same agent
    tracker.add_data(
        user_id=USER_ID, 
        token=1000, 
        model_name="gpt-4o",
        agent_name=agent_name
    )
    tracker.add_data(
        user_id=USER_ID, 
        token=500, 
        model_name="gpt-4o-mini",
        agent_name=agent_name
    )
    
    total_cost = tracker.get_agent_cost(agent_name)
    expected_cost = 0.01 + 0.0001875
    assert abs(total_cost - expected_cost) < 0.000001


def test_get_cost_summary(tracker, mock_s3_client):
    """Test getting cost summary for a user."""
    # Add usage data
    tracker.add_data(user_id=USER_ID, token=1000, model_name="gpt-4o")
    tracker.add_data(user_id=USER_ID, token=500, model_name="gpt-4o-mini")
    
    summary = tracker.get_cost_summary(USER_ID)
    
    assert "total_cost" in summary
    assert "total_tokens" in summary
    assert "total_calls" in summary
    assert "model_breakdown" in summary
    assert "average_cost_per_call" in summary
    
    assert summary["total_tokens"] == 1500
    assert summary["total_calls"] == 2
    assert "gpt-4o" in summary["model_breakdown"]
    assert "gpt-4o-mini" in summary["model_breakdown"]


def test_estimate_cost(tracker, mock_s3_client):
    """Test cost estimation for potential LLM calls."""
    # Test estimation with known model
    estimated_cost = tracker.estimate_cost("gpt-4o", 1000)
    assert estimated_cost == 0.01
    
    # Test estimation with unknown model
    estimated_cost = tracker.estimate_cost("unknown-model", 1000)
    assert estimated_cost == 0.002


def test_check_cost_limit(tracker, mock_s3_client):
    """Test cost limit checking functionality."""
    with patch("sherpa_ai.config.DAILY_COST_LIMIT", 1.0), \
         patch("sherpa_ai.config.COST_ALERT_THRESHOLD", 0.8):
        
        # Add some usage
        tracker.add_data(user_id=USER_ID, token=1000, model_name="gpt-4o")  # $0.01
        
        # Check cost limit
        result = tracker.check_cost_limit(USER_ID, estimated_cost=0.5)
        
        assert "current_cost" in result
        assert "estimated_cost" in result
        assert "total_cost" in result
        assert "daily_limit" in result
        assert "can_execute" in result
        assert "approaching_limit" in result
        
        assert result["current_cost"] == 0.01
        assert result["estimated_cost"] == 0.5
        assert result["total_cost"] == 0.51
        assert result["daily_limit"] == 1.0
        assert result["can_execute"] is True
        assert result["approaching_limit"] is False


def test_check_cost_limit_exceeded(tracker, mock_s3_client):
    """Test cost limit checking when limit is exceeded."""
    with patch("sherpa_ai.config.DAILY_COST_LIMIT", 0.01), \
         patch("sherpa_ai.config.COST_ALERT_THRESHOLD", 0.8):
        
        # Add usage that exceeds limit
        tracker.add_data(user_id=USER_ID, token=1000, model_name="gpt-4o")  # $0.01
        
        # Check cost limit
        result = tracker.check_cost_limit(USER_ID, estimated_cost=0.01)
        
        assert result["can_execute"] is False
        assert "exceeded" in result["message"].lower()


def test_pricing_with_custom_configuration(mock_s3_client):
    """Test that pricing works with custom configuration via environment variables."""
    from sherpa_ai.cost_tracking.pricing import PricingManager
    
    custom_pricing = {"gpt-4o": 0.015}  # Custom pricing
    
    with patch.dict("os.environ", {'MODEL_PRICING_JSON': json.dumps(custom_pricing)}):
        # Create a new tracker with custom pricing manager
        custom_pricing_manager = PricingManager()
        tracker = UserUsageTracker(
            db_name=TEST_DB_NAME, 
            db_url=TEST_DB_URL, 
            engine=engine,
            pricing_manager=custom_pricing_manager
        )
        delete_table_data(tracker)
        
        # Add data with custom pricing
        tracker.add_data(user_id=USER_ID, token=1000, model_name="gpt-4o")
        
        # Check that custom pricing was used
        data = tracker.get_data_since_last_reset(USER_ID)
        assert data[0]["cost"] == 0.015  # Custom pricing
        
        tracker.close_connection()


def test_pricing_with_custom_file(mock_s3_client):
    """Test that pricing works with custom configuration file."""
    from sherpa_ai.cost_tracking.pricing import PricingManager
    
    custom_pricing = {"gpt-4o": 0.020}  # Custom pricing
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(custom_pricing, f)
        temp_file = f.name
    
    try:
        # Create a new tracker with custom pricing manager from file
        custom_pricing_manager = PricingManager(config_path=temp_file)
        tracker = UserUsageTracker(
            db_name=TEST_DB_NAME, 
            db_url=TEST_DB_URL, 
            engine=engine,
            pricing_manager=custom_pricing_manager
        )
        delete_table_data(tracker)
        
        # Add data with custom pricing
        tracker.add_data(user_id=USER_ID, token=1000, model_name="gpt-4o")
        
        # Check that custom pricing was used
        data = tracker.get_data_since_last_reset(USER_ID)
        assert data[0]["cost"] == 0.020  # Custom pricing
        
        tracker.close_connection()
            
    finally:
        Path(temp_file).unlink()


def test_cost_tracking_with_different_models(tracker, mock_s3_client):
    """Test cost tracking with different models and their respective pricing."""
    models_and_expected_costs = [
        ("gpt-4o", 1000, 0.01),
        ("gpt-4o-mini", 1000, 0.000375),
        ("gpt-4-turbo", 1000, 0.02),
        ("claude-3-5-sonnet-20241022", 1000, 0.009),
        ("gemini-1.5-pro", 1000, 0.003125),
    ]
    
    for model, tokens, expected_cost in models_and_expected_costs:
        tracker.add_data(
            user_id=USER_ID,
            token=tokens,
            model_name=model
        )
    
    # Check total cost
    total_cost = tracker.get_user_cost(USER_ID)
    expected_total = sum(cost for _, _, cost in models_and_expected_costs)
    assert abs(total_cost - expected_total) < 0.000001
    
    # Check model breakdown
    summary = tracker.get_cost_summary(USER_ID)
    for model, _, expected_cost in models_and_expected_costs:
        assert model in summary["model_breakdown"]
        assert abs(summary["model_breakdown"][model] - expected_cost) < 0.000001
