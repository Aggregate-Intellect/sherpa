import sqlite3
import time


class UserUsageTracker:
    def __init__(self, db_name='token_countersaa.db', current_time=int(time.time()), max_daily_token=20000):
        self.conn = sqlite3.connect(db_name)
        self.create_table()
        self.max_daily_token = int(max_daily_token)
        self.current_time = current_time

    def create_table(self):
        create_token_reset_table_query  = '''
        CREATE TABLE IF NOT EXISTS usage_tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            token INTEGER,
            timestamp INTEGER,
            reset_timestamp BOOLEAN
        )
        '''
        self.conn.execute(create_token_reset_table_query)

        create_whitelist_table_query = '''
        CREATE TABLE IF NOT EXISTS whitelist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT
        )
        '''
        self.conn.execute(create_whitelist_table_query)

        self.conn.commit()

    def add_to_whitelist(self, user_id):
        insert_query = '''
        INSERT INTO whitelist (user_id)
        VALUES (?)
        '''
        self.conn.execute(insert_query, (user_id,))
        self.conn.commit()

    def get_all_whitelisted_ids(self):
        select_query = '''
        SELECT user_id FROM whitelist
        '''
        cursor = self.conn.execute(select_query)
        whitelisted_ids = [row[0] for row in cursor.fetchall()]
        return whitelisted_ids


    def get_whitelist_by_user_id(self, user_id):
        select_query = '''
        SELECT * FROM whitelist
        WHERE user_id = ?
        '''
        cursor = self.conn.execute(select_query, (user_id,))
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return data

    def is_in_whitelist(self, user_id):
        check_if_user = self.get_whitelist_by_user_id(user_id=user_id)

        if  check_if_user is not None and len(check_if_user) > 0:
            return True
        else:
            return False

    def add_data(self, combined_id, token, reset_timestamp=False):
        insert_query = '''
        INSERT INTO usage_tracker (user_id, token, timestamp, reset_timestamp)
        VALUES (?, ?, ?, ?)
        '''
        self.conn.execute(insert_query, (combined_id, token,
                          self.current_time, reset_timestamp))
        self.conn.commit()

    def get_data_since_last_reset(self, user_id):
        last_reset_info = self.get_last_reset_info(user_id)

        if last_reset_info is None or last_reset_info['id'] is None:
            select_query = '''
            SELECT * FROM usage_tracker
            WHERE user_id = ?
            '''
            cursor = self.conn.execute(select_query, (user_id,))
            columns = [col[0] for col in cursor.description]
            data = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return data

        select_query = '''
        SELECT * FROM usage_tracker
        WHERE user_id = ? AND id >= ?
        '''
        cursor = self.conn.execute(
            select_query, (user_id, last_reset_info['id']))
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        # Include the last_reset_id at the beginning
        data.insert(0, {'id': last_reset_info['id']})
        return data

    def get_sum_of_tokens_since_last_reset(self, user_id):
        data_since_last_reset = self.get_data_since_last_reset(user_id)

        if len(data_since_last_reset) == 1 and 'user_id' in data_since_last_reset[0]:
            return 0

        # Exclude the first row with last_reset_id
        token_sum = sum(row['token'] for row in data_since_last_reset[1:])
        return token_sum

    def reset_usage(self, combined_id, token_ammount):
        self.add_data(reset_timestamp=True,
                      token=token_ammount, combined_id=combined_id)

    def get_last_reset_info(self, combined_id):
        select_query = '''
        SELECT id, MAX(timestamp)
        FROM usage_tracker
        WHERE user_id = ? AND reset_timestamp = 1
        '''
        cursor = self.conn.execute(select_query, (combined_id,))
        row = cursor.fetchone()
        if row:
            last_reset_id, last_reset_timestamp = row
            return {'id': last_reset_id, 'timestamp': last_reset_timestamp}
        else:
            return None

    def check_usage(self, user_id, combined_id, token_ammount):
        user_is_whitelisted = self.is_in_whitelist(user_id)

        if user_is_whitelisted:
            return {'token-left': self.max_daily_token, 'can_excute': True, 'message': ''}
        else:
            last_reset_info = self.get_last_reset_info(combined_id=combined_id)
            time_since_last_reset = 99999


            if last_reset_info is not None and last_reset_info['timestamp'] is not None:

                time_since_last_reset = self.current_time - \
                    last_reset_info['timestamp']

            # If more than 24 hours have passed since last reset
            if time_since_last_reset != 0 and time_since_last_reset > 86400:
                print(f'TIMESTAMP DIFFERENT: {time_since_last_reset}')
                self.reset_usage(
                    combined_id=combined_id, token_ammount=token_ammount)
                return {'token-left': self.max_daily_token, 'can_excute': True, 'message': ''}
            else:
                total_token_since_last_reset = self.get_sum_of_tokens_since_last_reset(
                    user_id=combined_id)


                if self.max_daily_token - total_token_since_last_reset <= 0:
                    return {'token-left': self.max_daily_token - total_token_since_last_reset, 'can_excute': False,
                            'message': 'daily usage limit exceeded. you can try after 24 hours'}
                else:
                    self.add_data(combined_id=combined_id, token=token_ammount)
                    return {'token-left': self.max_daily_token - total_token_since_last_reset, "current_token": token_ammount, 'can_excute': True,
                            'message': ''}

    def get_all_data(self):
        select_query = '''
        SELECT * FROM usage_tracker
        '''
        cursor = self.conn.execute(select_query)
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return data

    def close_connection(self):
        self.conn.close()
