from fastapi import FastAPI, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from datetime import date
from typing import List

from models import AttendanceRecord, Base
from schemas import AttendanceCreate, AttendanceOut, AttendanceUpdate
from database import SessionLocal, engine

from sqlalchemy import extract

router = APIRouter()

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/attendance/{record_date}", response_model=AttendanceOut)
def read_attendance(record_date: date, db: Session = Depends(get_db)):
    record = db.query(AttendanceRecord).filter_by(date=record_date).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record

@router.post("/attendance/{record_date}", response_model=AttendanceOut)
def create_or_update_attendance(record_date: date, data: AttendanceCreate, db: Session = Depends(get_db)):
    record = db.query(AttendanceRecord).filter_by(date=record_date).first()
    if record:
        # Update
        for key, value in data.dict().items():
            setattr(record, key, value)
    else:
        # Create new
        record = AttendanceRecord(date=record_date, **data.dict())
        db.add(record)
    db.commit()
    db.refresh(record)
    return record



@router.get("/attendance/month/{year_month}", response_model=List[AttendanceOut])
def read_month_data(year_month: str, db: Session = Depends(get_db)):
    try:
        year, month = map(int, year_month.split("-"))
    except:
        raise HTTPException(status_code=400, detail="Invalid format. Use YYYY-MM.")
    records = db.query(AttendanceRecord)\
        .filter(extract("year", AttendanceRecord.date) == year)\
        .filter(extract("month", AttendanceRecord.date) == month)\
        .all()
    return records
