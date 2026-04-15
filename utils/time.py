# utils/time.py

from datetime import datetime

def time_ago(dt):
    now = datetime.utcnow()
    diff = now - dt

    seconds = diff.total_seconds()

    if seconds < 60:
        return "방금 전"
    elif seconds < 3600:
        return f"{int(seconds//60)}분 전"
    elif seconds < 86400:
        return f"{int(seconds//3600)}시간 전"
    else:
        return f"{int(seconds//86400)}일 전"