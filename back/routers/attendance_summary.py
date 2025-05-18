from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
from database import SessionLocal

from modules.time_utils import parse_time_str
from models import AttendanceRecord
from schemas import AttendanceDaySummaryResponse

from typing import List, Dict
from collections import defaultdict

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def calc_day_summary_backend(record: AttendanceRecord) -> Dict[str, any]:
    """1日の勤怠データから元データと計算値を分けて返す（バックエンド用）"""
    # 勤務時間などの計算
    if record.start_time and record.end_time:
        s = parse_time_str(record.start_time)
        e = parse_time_str(record.end_time)
        dt_s = datetime.combine(date.today(), s)
        dt_e = datetime.combine(date.today(), e)
        work_time = dt_e - dt_s
    else:
        work_time = timedelta(0)

    break_minutes = int(record.break_minutes or 0)
    break_time = timedelta(minutes=break_minutes)
    interruptions = record.interruptions or []
    interrupt_time = timedelta(0)
    for it in interruptions:
        its = parse_time_str(it.get("start"))
        ite = parse_time_str(it.get("end"))
        if its and ite:
            dt_its = datetime.combine(date.today(), its)
            dt_ite = datetime.combine(date.today(), ite)
            interrupt_time += (dt_ite - dt_its)
    total_break = break_time + interrupt_time
    actual_work = work_time - total_break
    side_job_minutes = int(record.side_job_minutes or 0)

    # 取得したままのデータ
    raw_data = {
        "id": record.id,
        "date": str(record.date),
        "start_time": record.start_time,
        "end_time": record.end_time,
        "break_minutes": record.break_minutes,
        "interruptions": record.interruptions,
        "side_job_minutes": record.side_job_minutes,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
        "comment": record.comment,
    }

    # 計算結果
    calc_data = {
        "work_hours": round(work_time.total_seconds() / 3600, 2),
        "break_hours": round(break_time.total_seconds() / 3600, 2),
        "interruptions_count": len(interruptions),
        "interrupt_hours": round(interrupt_time.total_seconds() / 3600, 2),
        "side_job_hours": round(side_job_minutes / 60, 2),
        "break_total_hours": round(total_break.total_seconds() / 3600, 2),
        "actual_work_hours": round(actual_work.total_seconds() / 3600, 2),
        "gross_hours": round((work_time.total_seconds() + side_job_minutes * 60 - interrupt_time.total_seconds()) / 3600, 2),
    }

    return {
        "raw": raw_data,
        "summary": calc_data
    }

# 1日の集計を計算するAPI
@router.get("/attendance/summary/daily/{record_date}", response_model=AttendanceDaySummaryResponse)
def get_day_detail_summary(record_date: date, db: Session = Depends(get_db)):
    record = db.query(AttendanceRecord).filter_by(date=record_date).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    result = calc_day_summary_backend(record)
    return result

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

