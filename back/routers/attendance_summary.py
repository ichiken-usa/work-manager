from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
from database import SessionLocal
from modules.time_utils import parse_time_str
from models import AttendanceRecord, AttendanceRecord, Holiday
from schemas import AttendanceDaySummaryResponse
from datetime import timedelta
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

@router.get("/attendance/summary/monthly/{year_month}", response_model=List[AttendanceDaySummaryResponse])
def get_monthly_summary(year_month: str, db: Session = Depends(get_db)):
    """
    指定した月の勤怠データを1日ずつ計算して返すAPI
    """
    try:
        year, month = map(int, year_month.split("-"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid format. Use YYYY-MM.")

    # 月の日付範囲を取得
    from calendar import monthrange
    days_in_month = monthrange(year, month)[1]
    all_dates = [date(year, month, day) for day in range(1, days_in_month + 1)]

    # 登録済みの勤怠データを取得
    registered_records = db.query(AttendanceRecord).filter(
        AttendanceRecord.date.in_(all_dates)
    ).all()

    # 日付ごとにデータを計算
    summaries = []
    records_by_date = {record.date: record for record in registered_records}

    for day in all_dates:
        if day in records_by_date:
            # 登録済みのデータがある場合
            record = records_by_date[day]
            summary = calc_day_summary_backend(record)
        else:
            # 登録されていない場合は空のデータを作成
            summary = {
                "raw": {
                    "id": None,
                    "date": str(day),
                    "start_time": None,
                    "end_time": None,
                    "break_minutes": 0,
                    "interruptions": [],
                    "side_job_minutes": 0,
                    "updated_at": None,
                    "comment": None,
                },
                "summary": {
                    "work_hours": 0.0,
                    "break_hours": 0.0,
                    "interruptions_count": 0,
                    "interrupt_hours": 0.0,
                    "side_job_hours": 0.0,
                    "break_total_hours": 0.0,
                    "actual_work_hours": 0.0,
                    "gross_hours": 0.0,
                },
            }
        summaries.append(summary)

    return summaries


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


@router.get("/attendance/forecast/{year_month}")
def forecast_monthly_work_hours(year_month: str, db: Session = Depends(get_db)):
    try:
        year, month = map(int, year_month.split("-"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid format. Use YYYY-MM.")

    # 月の日付範囲を取得
    from calendar import monthrange
    days_in_month = monthrange(year, month)[1]
    all_dates = [date(year, month, day) for day in range(1, days_in_month + 1)]

    # 登録済みの勤怠データを取得
    registered_records = db.query(AttendanceRecord).filter(
        AttendanceRecord.date.in_(all_dates)
    ).all()

    # 勤務日としての判定: 開始時刻と終了時刻が入力されている日
    work_days = {record.date for record in registered_records if record.start_time and record.end_time}

    # 祝日を取得
    holidays = db.query(Holiday).filter(Holiday.date.in_(all_dates)).all()
    holiday_dates = {holiday.date for holiday in holidays}

    # 未登録日を計算（勤務日と祝日を除外）
    unregistered_dates = set(all_dates) - work_days - holiday_dates

    # 土日を除外
    unregistered_dates = {d for d in unregistered_dates if d.weekday() < 5}  # weekday()が5以上は土日

    # 勤務時間の予測
    total_work_hours = 0
    for record in registered_records:
        if record.start_time and record.end_time:  # 勤務日としての判定
            start_time = parse_time_str(record.start_time)
            end_time = parse_time_str(record.end_time)
            work_time = (datetime.combine(date.today(), end_time) - datetime.combine(date.today(), start_time)).total_seconds() / 3600
            total_work_hours += work_time

    # 未登録日は1日8時間として加算
    total_work_hours += len(unregistered_dates) * 8

    return {
        "year_month": year_month,
        "registered_work_hours": total_work_hours - len(unregistered_dates) * 8,
        "predicted_work_hours": total_work_hours,
        "unregistered_days": len(unregistered_dates),
        "holiday_days": len(holiday_dates),
    }