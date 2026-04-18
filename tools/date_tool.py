from datetime import datetime


def days_until(date_str: str) -> int:
    target = datetime.strptime(date_str, "%Y-%m-%d").date()
    today = datetime.now().date()
    return (target - today).days
