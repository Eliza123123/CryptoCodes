from datetime import datetime


def is_top_of_minute():
    current_time = datetime.utcnow()
    return current_time.second == 0
