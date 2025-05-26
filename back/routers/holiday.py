from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import date
from typing import List

from models import Holiday
from database import SessionLocal
from schemas import HolidayCreate, HolidayOut

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/holidays/", response_model=List[HolidayOut])
def get_holidays(db: Session = Depends(get_db)):
    return db.query(Holiday).all()

@router.get("/holidays/{year_month}", response_model=List[HolidayOut])
def get_holidays_by_month(year_month: str, db: Session = Depends(get_db)):
    """
    指定した月の祝日を取得するAPI
    :param year_month: "YYYY-MM"形式の文字列
    :param db: データベースセッション
    :return: 指定月の祝日リスト
    """
    try:
        year, month = map(int, year_month.split("-"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid year_month format. Use 'YYYY-MM'.")

    holidays = db.query(Holiday).filter(
        Holiday.date >= date(year, month, 1),
        Holiday.date < date(year, month + 1, 1) if month < 12 else date(year + 1, 1, 1)
    ).all()

    return holidays

@router.post("/holidays/", response_model=HolidayOut)
def add_holiday(holiday: HolidayCreate, db: Session = Depends(get_db)):
    existing = db.query(Holiday).filter_by(date=holiday.date).first()
    if existing:
        raise HTTPException(status_code=400, detail="Holiday already exists")
    new_holiday = Holiday(date=holiday.date, name=holiday.name)
    db.add(new_holiday)
    db.commit()
    db.refresh(new_holiday)
    return new_holiday

@router.put("/holidays/{holiday_date}", response_model=HolidayOut)
def update_holiday(holiday_date: date, updated_holiday: HolidayCreate, db: Session = Depends(get_db)):
    """
    指定した日付の祝日を更新するAPI
    :param holiday_date: 更新対象の日付
    :param updated_holiday: 更新後の祝日データ
    :param db: データベースセッション
    :return: 更新された祝日データ
    """
    holiday = db.query(Holiday).filter_by(date=holiday_date).first()
    if not holiday:
        raise HTTPException(status_code=404, detail="Holiday not found")
    
    holiday.name = updated_holiday.name
    db.commit()
    db.refresh(holiday)
    return holiday

@router.delete("/holidays/{holiday_date}")
def delete_holiday(holiday_date: date, db: Session = Depends(get_db)):
    holiday = db.query(Holiday).filter_by(date=holiday_date).first()
    if not holiday:
        raise HTTPException(status_code=404, detail="Holiday not found")
    db.delete(holiday)
    db.commit()
    return {"detail": "Holiday deleted"}