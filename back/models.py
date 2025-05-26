from sqlalchemy import Column, Integer, Date, Time, JSON, DateTime, String
from datetime import datetime
from database import Base

def now_local():
    """タイムゾーン情報なしのローカル時間を返す"""
    return datetime.now()

class AttendanceRecord(Base):
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
    # 祝日を管理するモデル
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True, nullable=False, unique=True)
    name = Column(String, nullable=True)  # 祝日の名前（例: "元日", "建国記念の日"）