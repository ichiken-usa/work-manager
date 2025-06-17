from sqlalchemy import Column, Integer, Date, Time, JSON, DateTime, String
from datetime import datetime
from database import Base

def now_local():
    """
    タイムゾーン情報なしのローカル時間を返す。

    Returns:
        datetime: 現在のローカル時間。
    """
    return datetime.now()

class AttendanceRecord(Base):
    """
    勤怠記録を管理するモデル。

    Attributes:
        id (int): 主キー（自動採番）。
        date (Date): 勤怠対象日。
        start_time (str): 勤務開始時刻（例: "09:00"）。
        end_time (str): 勤務終了時刻（例: "18:00"）。
        break_minutes (int): 休憩時間（分単位）。
        interruptions (JSON): 中断時間リスト（例: [{"start": "12:00", "end": "13:00"}]）。
        side_job_minutes (int): 副業時間（分単位）。
        updated_at (DateTime): 最終更新日時。
        comment (str): コメント・備考欄。
    """
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True, nullable=False, unique=True)
    start_time = Column(String, nullable=True)
    end_time = Column(String, nullable=True)
    break_minutes = Column(Integer, nullable=True)
    interruptions = Column(JSON, nullable=True)
    side_job_minutes = Column(Integer, nullable=True)
    updated_at = Column(DateTime, nullable=True, default=now_local, onupdate=now_local)
    comment = Column(String, nullable=True)  # コメント欄

class Holiday(Base):
    """
    祝日を管理するモデル。

    Attributes:
        id (int): 主キー（自動採番）。
        date (Date): 祝日の日付。
        name (str): 祝日の名前（例: "元日", "建国記念の日"）。
    """
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True, nullable=False, unique=True)
    name = Column(String, nullable=True)  # 祝日の名前（例: "元日", "建国記念の日"）