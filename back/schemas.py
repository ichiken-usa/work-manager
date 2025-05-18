from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, time, datetime

# 1件の中断時間（例：休憩や離席）を表すモデル
class Interruption(BaseModel):
    start: str  # "HH:MM"形式の文字列
    end: str

# 勤怠情報の共通部分（基底クラス）
class AttendanceBase(BaseModel):
    start_time: Optional[str] = None         # 勤務開始時刻 "HH:MM"
    end_time: Optional[str] = None           # 勤務終了時刻 "HH:MM"
    break_minutes: Optional[int] = None
    interruptions: Optional[List[Interruption]] = []
    side_job_minutes: Optional[int] = None
    updated_at: Optional[datetime] = None
    comment: Optional[str] = None  # コメント欄

# 勤怠新規作成リクエスト用
class AttendanceCreate(AttendanceBase):
    pass

# 勤怠更新リクエスト用
class AttendanceUpdate(AttendanceBase):
    pass

# 勤怠情報レスポンス用
class AttendanceOut(AttendanceBase):
    date: date  # 勤怠日付

# 勤怠情報の集計結果用
class AttendanceSummary(BaseModel):
    work_hours: float
    break_hours: float
    interruptions_count: int
    interrupt_hours: float
    side_job_hours: float
    break_total_hours: float
    actual_work_hours: float
    gross_hours: float

# 勤怠情報の集計結果レスポンス用
class AttendanceDaySummaryResponse(BaseModel):
    raw: AttendanceOut
    summary: AttendanceSummary