import os
import threading

import pytest

from sherpa_ai.database.user_usage_tracker import UserUsageTracker
from sherpa_ai.verbose_loggers.base import BaseVerboseLogger
import shutil
import sqlite3

user_id = "test_id"

def create_testing_db_file(db_path):
    # Connect to the SQLite database (if it doesn't exist, it will be created)
    conn = sqlite3.connect(db_path)
    conn.close()
    print(f"Database file '{db_path}' created successfully.")

# Specify the path where you want to create the database file
db_path = "./tests/data/test_usage_counter.db"

# Call the function to create the database file
create_testing_db_file(db_path)


def test_usage_tracker_whitelist_add_and_get():
    check = os.path.exists("test_usage.db")
    if check:
        os.remove("test_usage.db")
    db = UserUsageTracker(db_name="test_usage.db", db_url="sqlite:///test_usage.db")
    db.add_to_whitelist(user_id=user_id)
    white_listed_id = db.get_all_whitelisted_ids()
    assert user_id in white_listed_id


def test_usage_checker():
    check = os.path.exists("test_usage.db")
    if check:
        os.remove("test_usage.db")
    db = UserUsageTracker(db_name="test_usage.db", db_url="sqlite:///test_usage.db" , )
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


def test_usage_reset_after_a_given_time():
    check = os.path.exists("test_usage.db")
    if check:
        os.remove("test_usage.db")
    db = UserUsageTracker(db_name="test_usage.db", db_url="sqlite:///test_usage.db")
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
        dormant_test_db_path = './tests/data/test_usage_counter.db'
        check = os.path.exists(dormant_test_db_path)
        if check:
            os.remove(dormant_test_db_path)

        # testing db file path
        active_test_db_path = "./test_usage.db"

        # Copy and rename the file
        shutil.copyfile(active_test_db_path, dormant_test_db_path)

    monkeypatch.setattr(UserUsageTracker, "upload_to_s3", mock_upload)


def test_download_db_from_s3(mock_download_from_s3):
    check = os.path.exists("test_usage.db")
    if check:
        os.remove("test_usage.db")
    UserUsageTracker.download_from_s3(
        db_name="test_usage.db", db_url="sqlite:///test_usage.db"
    )
    third_check = os.path.exists("test_usage.db")
    assert third_check, "downloading sqlight file has failed"


def test_whitelist_from_s3(mock_download_from_s3 , mock_upload_to_s3_from_s3):
    check = os.path.exists("test_usage.db")
    if not check:
        UserUsageTracker.download_from_s3(
            db_name="test_usage.db", db_url="sqlite:///test_usage.db"
        )
    db = UserUsageTracker(db_name="test_usage.db", db_url="sqlite:///test_usage.db")
    db.add_to_whitelist(user_id=user_id)
    db.upload_to_s3()
    os.remove("test_usage.db")
    UserUsageTracker.download_from_s3(
        db_name="test_usage.db", db_url="sqlite:///test_usage.db"
    )
    db2 = UserUsageTracker(db_name="test_usage.db", db_url="sqlite:///test_usage.db")
    white_listed_id = db2.get_all_whitelisted_ids()
    assert user_id in white_listed_id


def test_user_message_logger():
    check = os.path.exists("test_usage.db")
    if check:
        os.remove("test_usage.db")

    class TestLogger(BaseVerboseLogger):
        def __init__(self) -> None:
            self.message = ""

        def log(self, message):
            self.message = message

    logger = TestLogger()
    db = UserUsageTracker(
        db_name="test_usage.db",
        db_url="sqlite:///test_usage.db",
        verbose_logger=logger,
    )

    db.max_daily_token = 1000
    db.limit_time_size_in_hours = 9

    db.check_usage(token_amount="740", user_id="jack")
    assert logger.message == "", "it should not rich its 75% limit"
    db.check_usage(token_amount="11", user_id="jack")
    assert len(logger.message) > 0, "user should get a message at this amount."
