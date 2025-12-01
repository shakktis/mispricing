from __future__ import annotations
from datetime import date
import calendar as cal

def month_daycount(year: int, month: int) -> int:
    return cal.monthrange(year, month)[1]

def split_pre_post_days(meeting_date) -> tuple[int, int, int]:
    """
    meeting_date: datetime.date
    Returns (D_m, d_pre, d_post) for the month of meeting_date.
    d_pre counts days strictly before the meeting; d_post counts meeting day and after.
    """
    Dm = month_daycount(meeting_date.year, meeting_date.month)
    d_pre = meeting_date.day - 1
    d_post = Dm - d_pre
    return Dm, d_pre, d_post
