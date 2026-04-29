import calendar
from datetime import date, datetime

from fastapi import HTTPException


def parse_month(month: str) -> tuple[date, date]:
    try:
        parsed = datetime.strptime(month + "-01", "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=422, detail="month 格式错误，应为 YYYY-MM") from None

    days_in_month = calendar.monthrange(parsed.year, parsed.month)[1]
    start_date = date(parsed.year, parsed.month, 1)
    end_date = date(parsed.year, parsed.month, days_in_month)
    return start_date, end_date


def validate_date_range(start_date: date, end_date: date) -> None:
    if start_date > end_date:
        raise HTTPException(status_code=422, detail="开始日期不能晚于结束日期")
