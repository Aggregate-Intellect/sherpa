import time
from anyio import Path
import boto3
from sqlalchemy import TIMESTAMP, Boolean, Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import sherpa_ai.config as cfg
from sherpa_ai.verbose_loggers.base import BaseVerboseLogger
from sherpa_ai.verbose_loggers.verbose_loggers import DummyVerboseLogger

Base = declarative_base()

import boto3


class UsageTracker(Base):
    __tablename__ = "usage_tracker"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String)
    token = Column(Integer)
    timestamp = Column(Integer)
    reset_timestamp = Column(Boolean)
    reminded_timestamp = Column(Boolean)


class Whitelist(Base):
    __tablename__ = "whitelist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String)


class UserUsageTracker:
    def __init__(
        self,
        db_name=cfg.DB_NAME,
        verbose_logger: BaseVerboseLogger = DummyVerboseLogger(),
    ):
        self.engine = create_engine(db_name)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.create_table()
        self.max_daily_token = float(cfg.DAILY_TOKEN_LIMIT)
        self.verbose_logger = verbose_logger
        self.is_reminded = False

    def download_from_s3(self, bucket_name, s3_file_key, local_file_path):
        file_path = Path('./token_counter.db')
        if not file_path.exists():
            s3 = boto3.client('s3')
            s3.download_file(bucket_name, s3_file_key, local_file_path)

    def upload_to_s3(self, local_file_path, bucket_name, s3_file_key):
        s3 = boto3.client("s3")
        s3.upload_file(local_file_path, bucket_name, s3_file_key)

    def create_table(self):
        Base.metadata.create_all(self.engine)

    def add_to_whitelist(self, user_id):
        user = Whitelist(user_id=user_id)
        self.session.add(user)
        self.session.commit()
        if not cfg.FLASK_DEBUG:
            self.upload_to_s3(
                "./token_counter.db", "sherpa-sqlight", "token_counter.db"
            )

    def get_all_whitelisted_ids(self):
        whitelisted_ids = [user.user_id for user in self.session.query(Whitelist).all()]
        return whitelisted_ids

    def get_whitelist_by_user_id(self, user_id):
        data = self.session.query(Whitelist).filter_by(user_id=user_id).all()
        return [{"id": item.id, "user_id": item.user_id} for item in data]

    def is_in_whitelist(self, user_id):
        return bool(self.get_whitelist_by_user_id(user_id))
    
    def add_and_check_data(self, combined_id, token, reset_timestamp=False , reminded_timestamp=False):
        self.add_data(combined_id=combined_id , token=token, reset_timestamp=reset_timestamp, reminded_timestamp=reminded_timestamp)
        self.token_left_calculator(combined_id=combined_id)

    def add_data(self, combined_id, token, reset_timestamp=False , reminded_timestamp=False):
        data = UsageTracker(
            user_id=combined_id,
            token=token,
            timestamp=int(time.time()),
            reset_timestamp=reset_timestamp,
            reminded_timestamp=reminded_timestamp
        )
        self.session.add(data)
        self.session.commit()

    def percentage_used(self , combined_id):
        total_token_since_last_reset = self.get_sum_of_tokens_since_last_reset(
                user_id=combined_id
            )
        return  (total_token_since_last_reset*100)/self.max_daily_token 


    def token_left_calculator(self, combined_id):
        split_parts = combined_id.split('_')
        user_id = ""
        if len(split_parts) > 0:
            user_id = split_parts[0]

        user_is_whitelisted = self.is_in_whitelist(user_id)
        self.is_reminded = self.check_if_reminded(combined_id=combined_id)
        if not user_is_whitelisted and not self.is_reminded:
            if self.percentage_used(combined_id=combined_id) > 75 and not self.is_reminded:
                self.add_data(combined_id=combined_id , token=0 , reminded_timestamp=True )

                self.verbose_logger.log(
                'hi friend, you have used up 75% of your daily token limit. once you go over the limit there will be a 24 cool down period after which you can continue using Sherpa! be awesome!')
                
    def get_data_since_last_reset(self, user_id):
        last_reset_info = self.get_last_reset_info(user_id)

        if last_reset_info is None or last_reset_info["id"] is None:
            data = self.session.query(UsageTracker).filter_by(user_id=user_id).all()
            return [
                {
                    "id": item.id,
                    "user_id": item.user_id,
                    "token": item.token,
                    "timestamp": item.timestamp,
                    "reset_timestamp": item.reset_timestamp,
                    "reminded_timestamp": item.reminded_timestamp,
                }
                for item in data
            ]

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
                "timestamp": item.timestamp,
                "reset_timestamp": item.reset_timestamp,
                "reminded_timestamp": item.reminded_timestamp,
            }
            for item in data
        ]
    
    def check_if_reminded(self,combined_id):
        data_list = self.get_data_since_last_reset(combined_id)
        is_reminded_true = any(item.get('reminded_timestamp', False) for item in data_list)
        
        return is_reminded_true
        

    def get_sum_of_tokens_since_last_reset(self, user_id):
        data_since_last_reset = self.get_data_since_last_reset(user_id)

        if len(data_since_last_reset) == 1 and "user_id" in data_since_last_reset[0]:
            return 0

        token_sum = sum(item["token"] for item in data_since_last_reset[1:])
        return token_sum

    def reset_usage(self, combined_id, token_amount):
        self.add_and_check_data(combined_id=combined_id,token=token_amount, reset_timestamp=True)

    def get_last_reset_info(self, combined_id):
        data = (
            self.session.query(UsageTracker.id, UsageTracker.timestamp)
            .filter(
                UsageTracker.user_id == combined_id, UsageTracker.reset_timestamp == 1
            )
            .order_by(UsageTracker.timestamp.desc())
            .first()
        )
        if data:
            last_reset_id, last_reset_timestamp = data
            return {"id": last_reset_id, "timestamp": last_reset_timestamp}
        else:
            return None

    def seconds_to_hms(self, seconds):
        remaining_seconds = int(float(cfg.LIMIT_TIME_SIZE_IN_HOURS) * 3600 - seconds)
        hours = remaining_seconds // 3600
        minutes = (remaining_seconds % 3600) // 60
        seconds = remaining_seconds % 60

        return f"{hours} hours : {minutes} min : {seconds} sec"

    def check_usage(self, user_id, combined_id, token_amount):
        user_is_whitelisted = self.is_in_whitelist(user_id)

        if user_is_whitelisted:
            return {
                "token-left": self.max_daily_token,
                "can_excute": True,
                "message": "",
                "time_left": "",
            }
        else:
            last_reset_info = self.get_last_reset_info(combined_id=combined_id)
            time_since_last_reset = 99999

            if last_reset_info is not None and last_reset_info["timestamp"] is not None:
                time_since_last_reset = int(time.time()) - last_reset_info["timestamp"]

            if time_since_last_reset != 0 and time_since_last_reset > 3600 * float(
                cfg.LIMIT_TIME_SIZE_IN_HOURS
            ):
                print(f"TIMESTAMP DIFFERENT: {time_since_last_reset}")
                self.reset_usage(combined_id=combined_id, token_amount=token_amount)
                return {
                    "token-left": self.max_daily_token,
                    "can_excute": True,
                    "message": "",
                    "time_left": self.seconds_to_hms(time_since_last_reset),
                }
            else:
                total_token_since_last_reset = self.get_sum_of_tokens_since_last_reset(
                    user_id=combined_id
                )

                if self.max_daily_token - total_token_since_last_reset <= 0:
                    return {
                        "token-left": self.max_daily_token
                        - total_token_since_last_reset,
                        "can_excute": False,
                        "message": "daily usage limit exceeded. you can try after 24 hours",
                        "time_left": self.seconds_to_hms(time_since_last_reset),
                    }
                else:
                    self.add_and_check_data(combined_id=combined_id, token=token_amount)
                    return {
                        "token-left": self.max_daily_token
                        - total_token_since_last_reset,
                        "current_token": token_amount,
                        "can_excute": True,
                        "message": "",
                        "time_left": self.seconds_to_hms(time_since_last_reset),
                    }

    def get_all_data(self):
        data = self.session.query(UsageTracker).all()
        return [
            {
                "id": item.id,
                "user_id": item.user_id,
                "token": item.token,
                "timestamp": item.timestamp,
                "reset_timestamp": item.reset_timestamp,
            }
            for item in data
        ]

    def close_connection(self):
        self.session.close()
