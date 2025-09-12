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
