from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
from models import AttendanceRecord  # 必要なものだけをインポート
from database import SessionLocal

from typing import List, Dict
from collections import defaultdict

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ⬛ 1. 月別サマリーAPI
@router.get("/attendance/summary/12months")
def get_monthly_summary(db: Session = Depends(get_db)):
    today = date.today()
    summaries = []
    for i in range(12):
        # iヶ月前の月初を取得
        month_date = (today.replace(day=1) - timedelta(days=30*i))
        start = month_date.replace(day=1)
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1, day=1)
        else:
            end = start.replace(month=start.month + 1, day=1)

        records = db.query(AttendanceRecord).filter(
            AttendanceRecord.date >= start,
            AttendanceRecord.date < end
        ).all()

        total_minutes = 0
        working_days = 0

        for r in records:
            if r.start_time and r.end_time:
                minutes = ((datetime.combine(date.min, r.end_time) -
                            datetime.combine(date.min, r.start_time)).seconds) / 60
                minutes -= r.break_minutes or 0
                total_minutes += minutes
                working_days += 1

        summaries.append({
            "month": start.strftime("%Y-%m"),
            "working_days": working_days,
            "total_work_minutes": total_minutes
        })

    summaries.reverse()  # 昇順（月初から最新）
    return summaries

# ⬛ 2. 日別サマリーAPI
@router.get("/attendance/summary/daily/{month}")
def get_daily_summary(month: str, db: Session = Depends(get_db)):
    start = datetime.strptime(month, "%Y-%m").date()
    if start.month == 12:
        end = date(start.year + 1, 1, 1)
    else:
        end = date(start.year, start.month + 1, 1)

    records = db.query(AttendanceRecord).filter(
        AttendanceRecord.date >= start,
        AttendanceRecord.date < end
    ).all()

    day_map = defaultdict(float)

    for r in records:
        if r.start_time and r.end_time:
            minutes = ((datetime.combine(date.min, r.end_time) -
                        datetime.combine(date.min, r.start_time)).seconds) / 60
            minutes -= r.break_minutes or 0
            day_map[r.date.strftime("%Y-%m-%d")] += minutes

    result = [{"date": k, "work_minutes": v} for k, v in sorted(day_map.items())]
    return result
