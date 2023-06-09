from datetime import datetime


def is_top_of_minute():
    current_time = datetime.utcnow()
    return current_time.second == 0


def fifteen_second_intervals():
    current_time = datetime.utcnow()
    return current_time.second in [0, 15, 30, 45]
