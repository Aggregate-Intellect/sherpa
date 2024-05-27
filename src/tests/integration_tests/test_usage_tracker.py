import os
import threading

import pytest

from sherpa_ai.database.user_usage_tracker import UserUsageTracker
from sherpa_ai.verbose_loggers.base import BaseVerboseLogger
import shutil
import sqlite3

user_id = "test_id"

TEST_DB_NAME = "test_usage.db"
TEST_DB_URL = "sqlite:///test_usage.db"


@pytest.fixture
def db_setup_teardown():
    if os.path.exists(TEST_DB_NAME):
        os.remove(TEST_DB_NAME)
    yield

    if os.path.exists(TEST_DB_NAME):
        os.remove(TEST_DB_NAME)


@pytest.fixture
def db_setup_s3_bucket():

    db_path = "./tests/data/test_usage_counter.db"
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        conn.close()
        print(f"Database file '{db_path}' created successfully.")
    yield
    if os.path.exists(db_path):
        os.remove(db_path)


def test_usage_tracker_add_to_whitelist(db_setup_teardown):
    db = UserUsageTracker(db_name=TEST_DB_NAME, db_url=TEST_DB_URL)
    db.add_to_whitelist(user_id=user_id)
    white_listed_id = db.get_all_whitelisted_ids()
    assert user_id in white_listed_id


def test_check_usage_limits_remaining_tokens(db_setup_teardown):
    db = UserUsageTracker(
        db_name=TEST_DB_NAME,
        db_url=TEST_DB_URL,
    )
    db.max_daily_token = 2000
    db.limit_time_size_in_hours = 0.1
    check_usage = db.check_usage(token_amount="3000", user_id="jack")
    assert check_usage["can_execute"] == False
    check_usage = db.check_usage(token_amount="1000", user_id="jack")
    assert check_usage["can_execute"] == True
    check_usage = db.check_usage(token_amount="1000", user_id="jack")
    assert check_usage["can_execute"] == True and check_usage["token-left"] == 1000
    check_usage = db.check_usage(token_amount="1000", user_id="jack")
    assert check_usage["can_execute"] == False and check_usage["token-left"] == 0


def test_usage_reset_after_a_given_time(db_setup_teardown):
    db = UserUsageTracker(db_name=TEST_DB_NAME, db_url=TEST_DB_URL)
    db.max_daily_token = 2000
    db.limit_time_size_in_hours = 0.001  # 3.6 seconds
    db.check_usage(token_amount="2000", user_id="jack")
    check_usage = db.check_usage(token_amount="10", user_id="jack")
    assert check_usage["can_execute"] == False

    # check if the usage tracker has been updated after 4 seconds
    timer = threading.Timer(4.0, (lambda: ""))
    timer.start()
    timer.join()
    check_usage = db.check_usage(token_amount="10", user_id="jack")
    assert check_usage["can_execute"] == True


@pytest.fixture
def mock_download_from_s3(monkeypatch):
    # by copying and renaming this function mocks downloading from sqlight file
    def mock_download(*args, **kwargs):
        # sqlight db file path which acts as s3 bucket
        dormant_test_db_path = "./tests/data/test_usage_counter.db"

        # testing db file path
        active_test_db_path = "./test_usage.db"

        # Copy and rename the file
        shutil.copyfile(dormant_test_db_path, active_test_db_path)

    monkeypatch.setattr(UserUsageTracker, "download_from_s3", mock_download)


@pytest.fixture
def mock_upload_to_s3_from_s3(monkeypatch):
    # by copying and renaming the testing sqlight db file to the location of the dormant file this function mocks uploading to s3 bucket.
    def mock_upload(*args, **kwargs):
        # sqlight db file path which acts as s3 bucket
        dormant_test_db_path = "./tests/data/test_usage_counter.db"
        check = os.path.exists(dormant_test_db_path)
        if check:
            os.remove(dormant_test_db_path)

        # testing db file path
        active_test_db_path = "./test_usage.db"

        # Copy and rename the file
        shutil.copyfile(active_test_db_path, dormant_test_db_path)

    monkeypatch.setattr(UserUsageTracker, "upload_to_s3", mock_upload)


def test_download_db_from_s3(
    db_setup_s3_bucket, mock_download_from_s3, db_setup_teardown
):
    UserUsageTracker.download_from_s3(
        db_name="test_usage.db", db_url="sqlite:///test_usage.db"
    )
    third_check = os.path.exists("test_usage.db")
    assert third_check, "downloading sqlight file has failed"


def test_whitelist_from_s3(
    db_setup_s3_bucket,
    mock_download_from_s3,
    mock_upload_to_s3_from_s3,
    db_setup_teardown,
):
    db = UserUsageTracker(db_name=TEST_DB_NAME, db_url=TEST_DB_URL)
    db.add_to_whitelist(user_id=user_id)
    db.upload_to_s3()
    os.remove(TEST_DB_NAME)
    UserUsageTracker.download_from_s3(db_name=TEST_DB_NAME, db_url=TEST_DB_URL)
    db2 = UserUsageTracker(db_name=TEST_DB_NAME, db_url=TEST_DB_URL)
    white_listed_id = db2.get_all_whitelisted_ids()
    assert user_id in white_listed_id


def test_user_message_logger(db_setup_teardown):
    class TestLogger(BaseVerboseLogger):
        def __init__(self) -> None:
            self.message = ""

        def log(self, message):
            self.message = message

    logger = TestLogger()
    db = UserUsageTracker(
        db_name=TEST_DB_NAME,
        db_url=TEST_DB_URL,
        verbose_logger=logger,
    )

    db.max_daily_token = 1000
    db.limit_time_size_in_hours = 9

    db.check_usage(token_amount="740", user_id="jack")
    assert logger.message == "", "it should not reach its 75% limit"
    db.check_usage(token_amount="11", user_id="jack")
    assert len(logger.message) > 0, "user should get a message at this amount."
