"""
このモジュールは、FastAPIアプリケーションのエントリーポイントを提供します。

Attributes:
    app (FastAPI): FastAPIアプリケーションのインスタンス。

Routes:
    /api/attendance: 勤怠データのCRUD操作を提供するエンドポイント。
    /api/attendance_summary: 勤怠データの集計結果を提供するエンドポイント。
    /api/holiday: 休日データのCRUD操作を提供するエンドポイント。
"""

from fastapi import FastAPI
from routers import attendance, attendance_summary, holiday

app = FastAPI()

# ルータを登録
app.include_router(attendance.router, prefix="/api")
app.include_router(attendance_summary.router, prefix="/api")
app.include_router(holiday.router, prefix="/api")

@app.get("/")
def read_root():
    """
    ルートエンドポイント。

    Returns:
        dict: サーバーの動作確認用メッセージ。
    """
    return {"Hello": "World"}