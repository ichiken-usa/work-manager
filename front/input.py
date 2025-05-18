import streamlit as st
from datetime import datetime, time, date
import pandas as pd

from modules.time_utils import parse_time_str
from modules.api_client import fetch_attendance_data, fetch_monthly_attendance, save_attendance, fetch_daily_summary
from modules.session import init_session_state
from modules.ui_components import show_last_updated, show_attendance_form, render_calendar_only, get_safe
from modules.attendance_utils import calc_day_summary
from settings import API_URL, DEFAULT_START_TIME, DEFAULT_END_TIME, DEFAULT_BREAK_MINUTES, DEFAULT_SIDE_JOB_MINUTES, DEFAULT_START_INTERRUPTION, DEFAULT_END_INTERRUPTION, DEFAULT_INTERRUPTION


#勤怠入力ページのメイン処理。
#セッション初期化、データ取得、フォーム表示を行う。


PAGE_NAME = "input"
session_state_list = ["last_payload", "saved", "deleted", "error"]

# ページ遷移時にセッションステートを初期化する
init_session_state(PAGE_NAME, session_state_list)

st.title("勤怠入力")
record_date: date = st.date_input("対象日付", date.today())

# --- カレンダー用データの取得 ---
month_str = record_date.strftime("%Y-%m")
records = fetch_monthly_attendance(month_str)

# 日付入力
input_dates_set = set(pd.to_datetime([
    r["date"] for r in records
    if r.get("start_time") or r.get("end_time") or r.get("side_job_minutes", 0) > 0
]).date)
render_calendar_only(record_date.year, record_date.month, input_dates_set, select_key="selected_date")


# 勤怠データをサマリーAPIから取得
data = fetch_daily_summary(record_date)
if data is None:
    st.error("データ取得に失敗したため、入力欄を表示できません。")
    st.stop()

# dataは{"raw": {...}, "summary": {...}}の形式
raw = data.get("raw", {})
summary = data.get("summary", {})

# 取得したデータが空でない場合は、各値を設定
if raw:
    start_time = raw.get("start_time") if raw.get("start_time") else DEFAULT_START_TIME
    end_time = raw.get("end_time") if raw.get("end_time") else DEFAULT_END_TIME
    break_minutes = int(raw.get("break_minutes", DEFAULT_BREAK_MINUTES))
    interruptions = raw.get("interruptions", DEFAULT_INTERRUPTION)
    side_job_minutes = int(raw.get("side_job_minutes", DEFAULT_SIDE_JOB_MINUTES))
    updated_at = raw.get("updated_at")
    comment = raw.get("comment", "")
    st.markdown(f"{record_date.strftime('%Y/%m/%d')} 🟢 登録済み")
else:
    st.info("この日付のデータはありません。新規入力できます。")
    start_time = DEFAULT_START_TIME
    end_time = DEFAULT_END_TIME
    break_minutes = DEFAULT_BREAK_MINUTES
    interruptions = DEFAULT_INTERRUPTION
    side_job_minutes = DEFAULT_SIDE_JOB_MINUTES
    updated_at = None
    comment = ""
    st.markdown(f"{record_date.strftime('%Y/%m/%d')} 🔴 未登録")

# 最終更新日時を表示
show_last_updated(updated_at)

# summaryがあれば集計値を表示
if summary:
    df = pd.DataFrame([
        ["勤務開始", str(raw.get("start_time", ""))],
        ["勤務終了", str(raw.get("end_time", ""))],
        ["勤務時間", f'{summary.get("work_hours", 0):.2f} 時間'],
        ["休憩時間", f'{summary.get("break_hours", 0):.2f} 時間'],
        ["中断回数", str(summary.get("interruptions_count", 0))],
        ["中断時間", f'{summary.get("interrupt_hours", 0):.2f} 時間'],
        ["副業時間", f'{summary.get("side_job_hours", 0):.2f} 時間'],
        ["休憩＋中断合計", f'{summary.get("break_total_hours", 0):.2f} 時間'],
        ["実働時間", f'{summary.get("actual_work_hours", 0):.2f} 時間'],
        ["総拘束時間", f'{summary.get("gross_hours", 0):.2f} 時間'],
    ], columns=["項目", "値"])
    st.table(df)

# 勤怠入力フォームを表示
form_result = show_attendance_form(
    record_date, start_time, end_time, break_minutes, interruptions, side_job_minutes, comment
)

if form_result["can_save"]:
    if st.button("保存"):
        payload = {
            "date": record_date.isoformat(),
            "start_time": form_result["start_time"].strftime("%H:%M") if form_result["start_time"] else "",
            "end_time": form_result["end_time"].strftime("%H:%M") if form_result["end_time"] else "",
            "break_minutes": form_result["break_minutes"],
            "interruptions": form_result["interruptions"],
            "side_job_minutes": form_result["side_job_minutes"],
            "comment": form_result["comment"]
        }
        st.session_state["last_payload"] = payload
        success = save_attendance(record_date.isoformat(), payload, API_URL)
        if success:
            st.session_state["saved"] = True
            #リロード
            st.rerun()
        else:
            st.error("保存に失敗しました")

# リロード後も残すためにセッションを見て成功表示
if st.session_state.get("saved"):
    if st.session_state['saved']:
        st.success("保存しました")
        st.session_state["saved"] = False 

# リロード後もpayloadを表示
if "last_payload" in st.session_state:
    st.write("直近の送信データ（payload）:", st.session_state["last_payload"])