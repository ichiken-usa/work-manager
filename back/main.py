from fastapi import FastAPI
from routers import attendance, attendance_summary


app = FastAPI()


app.include_router(attendance.router, prefix="/api")
app.include_router(attendance_summary.router, prefix="/api")


@app.get("/")
def read_root():
    return {"Hello": "World"}

