# 勤怠データの集計・ロジック系
from datetime import datetime, timedelta, date
from typing import Any, Dict, List
from settings import DEFAULT_SIDE_JOB_MINUTES
from modules.time_utils import parse_time_str

def aggregate_attendance(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    勤怠データのリストから集計値を計算して返す。

    Returns:
        {
            "work_total_hours": float,
            "break_total_hours": float,
            "interrupt_total_hours": float,
            "side_job_total_hours": float,
            "gross_total_hours": float,
            "actual_work_hours": float,
            "work_days": int
        }
    """

    work_total = timedelta()
    break_total = 0
    interrupt_total = timedelta()
    side_job_total = 0

    for data in records:
        # 勤務合計
        if data.get("start_time") and data.get("end_time"):
            s = parse_time_str(data.get("start_time"))
            e = parse_time_str(data.get("end_time"))
            dt_s = datetime.combine(date.today(), s)
            dt_e = datetime.combine(date.today(), e)
            work_total += (dt_e - dt_s)

        # 休憩合計
        break_total += int(data.get("break_minutes", 0))

        # 中断合計
        interruptions = data.get("interruptions", 0)
        for it in interruptions:
            its = parse_time_str(it.get("start"))
            ite = parse_time_str(it.get("end"))
            if its and ite:
                dt_its = datetime.combine(date.today(), its)
                dt_ite = datetime.combine(date.today(), ite)
                interrupt_total += (dt_ite - dt_its)

        # 副業合計
        side_job_total += int(data.get("side_job_minutes", DEFAULT_SIDE_JOB_MINUTES))

    work_total_hours = work_total.total_seconds() / 3600
    break_total_hours = break_total / 60
    interrupt_total_hours = interrupt_total.total_seconds() / 3600
    side_job_total_hours = side_job_total / 60

    gross_total_hours = work_total_hours + side_job_total_hours  # 総勤務時間
    actual_work_hours = work_total_hours - break_total_hours - interrupt_total_hours  # 実働時間

    work_days = len([
        r for r in records
        if r.get("start_time") and r.get("end_time")
    ])

    return {
        "work_total_hours": work_total_hours,
        "break_total_hours": break_total_hours,
        "interrupt_total_hours": interrupt_total_hours,
        "side_job_total_hours": side_job_total_hours,
        "gross_total_hours": gross_total_hours,
        "actual_work_hours": actual_work_hours,
        "work_days": work_days
    }

def calc_day_summary(data):
    """1日の勤怠データから勤務時間・休憩時間・実働時間を計算して返す"""
    # 勤務時間
    work_time = None
    if data.get("start_time") and data.get("end_time"):
        s = parse_time_str(data["start_time"])
        e = parse_time_str(data["end_time"])
        dt_s = datetime.combine(date.today(), s)
        dt_e = datetime.combine(date.today(), e)
        work_time = dt_e - dt_s
    else:
        work_time = timedelta(0)

    # 休憩時間
    break_minutes = int(data.get("break_minutes", 0))
    break_time = timedelta(minutes=break_minutes)

    # 中断時間
    interruptions = data.get("interruptions", [])
    interrupt_time = timedelta(0)
    for it in interruptions:
        its = parse_time_str(it.get("start"))
        ite = parse_time_str(it.get("end"))
        if its and ite:
            dt_its = datetime.combine(date.today(), its)
            dt_ite = datetime.combine(date.today(), ite)
            interrupt_time += (dt_ite - dt_its)

    # 休憩合計
    total_break = break_time + interrupt_time

    # 実働時間
    actual_work = work_time - total_break

    return {
        "勤務時間": work_time.total_seconds() / 3600,
        "休憩時間": total_break.total_seconds() / 3600,
        "実働時間": actual_work.total_seconds() / 3600
    }