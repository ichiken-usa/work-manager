"""
このモジュールは、Pydanticを使用してデータ検証とシリアライズを行うためのスキーマを定義します。

Classes:
    Interruption: 中断時間を表すスキーマ。
    AttendanceBase: 勤怠情報の共通部分を表す基底スキーマ。
    AttendanceCreate: 勤怠新規作成リクエスト用スキーマ。
    AttendanceUpdate: 勤怠更新リクエスト用スキーマ。
    AttendanceOut: 勤怠情報レスポンス用スキーマ。
    AttendanceSummary: 勤怠情報の集計結果スキーマ。
    AttendanceDaySummaryResponse: 勤怠情報の集計結果レスポンススキーマ。
    MonthlyAggregateSummary: 月次集計結果スキーマ。
    HolidayBase: 休日情報の共通部分を表す基底スキーマ。
    HolidayCreate: 休日新規作成リクエスト用スキーマ。
    HolidayOut: 休日情報レスポンス用スキーマ。
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, time, datetime

# 1件の中断時間（例：休憩や離席）を表すモデル
class Interruption(BaseModel):
    """
    モデル: 中断時間を表す

    Attributes:
        start (str): 中断開始時刻（"HH:MM"形式）。
        end (str): 中断終了時刻（"HH:MM"形式）。
    """
    start: str  # "HH:MM"形式の文字列
    end: str

# 勤怠情報の共通部分（基底クラス）
class AttendanceBase(BaseModel):
    """
    モデル: 勤怠情報の共通部分

    Attributes:
        start_time (Optional[str]): 勤務開始時刻（"HH:MM"形式）。
        end_time (Optional[str]): 勤務終了時刻（"HH:MM"形式）。
        break_minutes (Optional[int]): 休憩時間（分単位）。
        interruptions (Optional[List[Interruption]]): 中断時間のリスト。
        side_job_minutes (Optional[int]): 副業時間（分単位）。
        updated_at (Optional[datetime]): 最終更新日時。
        comment (Optional[str]): コメント欄。
    """
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    break_minutes: Optional[int] = None
    interruptions: Optional[List[Interruption]] = []
    side_job_minutes: Optional[int] = None
    updated_at: Optional[datetime] = None
    comment: Optional[str] = None

# 勤怠新規作成リクエスト用
class AttendanceCreate(AttendanceBase):
    """
    モデル: 勤怠新規作成リクエスト用
    """
    pass

# 勤怠更新リクエスト用
class AttendanceUpdate(AttendanceBase):
    """
    モデル: 勤怠更新リクエスト用
    """
    pass

# 勤怠情報レスポンス用
class AttendanceOut(AttendanceBase):
    """
    モデル: 勤怠情報レスポンス用

    Attributes:
        date (date): 勤怠日付。
    """
    date: date

# 勤怠情報の集計結果用
class AttendanceSummary(BaseModel):
    """
    モデル: 勤怠情報の集計結果

    Attributes:
        work_hours (float): 勤務時間。
        break_hours (float): 休憩時間。
        interruptions_count (int): 中断回数。
        interrupt_hours (float): 中断時間。
        side_job_hours (float): 副業時間。
        break_total_hours (float): 休憩時間の合計。
        actual_work_hours (float): 実働時間。
        gross_hours (float): 総勤務時間。
    """
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
    """
    モデル: 勤怠情報の集計結果レスポンス

    Attributes:
        raw (AttendanceOut): 勤怠情報の詳細。
        summary (AttendanceSummary): 勤怠情報の集計結果。
    """
    raw: AttendanceOut
    summary: AttendanceSummary

    class Config:
        from_attributes = True  # 旧: orm_mode = True

class MonthlyAggregateSummary(BaseModel):
    """
    モデル: 月次集計結果

    Attributes:
        work_total_hours (float): 勤務時間の合計。
        break_total_hours (float): 休憩時間の合計。
        interrupt_total_hours (float): 中断時間の合計。
        side_job_total_hours (float): 副業時間の合計。
        gross_total_hours (float): 総勤務時間。
        actual_work_hours (float): 実働時間。
        work_days (int): 勤務日数。
        gross_days (int): グロス日数。
    """
    work_total_hours: float
    break_total_hours: float
    interrupt_total_hours: float
    side_job_total_hours: float
    gross_total_hours: float
    actual_work_hours: float
    work_days: int
    gross_days: int

    class Config:
        from_attributes = True  # Pydantic v2対応

class HolidayBase(BaseModel):
    """
    モデル: 休日情報の共通部分

    Attributes:
        date (date): 休日の日付。
        name (str): 休日の名前。
    """
    date: date
    name: str

class HolidayCreate(HolidayBase):
    """
    モデル: 休日新規作成リクエスト用
    """
    pass

class HolidayOut(HolidayBase):
    """
    モデル: 休日情報レスポンス用

    Attributes:
        id (int): 休日のID。
    """
    id: int

    class Config:
        from_attributes = True