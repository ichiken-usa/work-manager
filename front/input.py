import streamlit as st
from datetime import datetime, time, date

from modules.time_utils import parse_time_str
from modules.api_client import fetch_attendance_data
from modules.session import init_session_state
from modules.ui_components import show_last_updated, show_attendance_form

from settings import API_URL, DEFAULT_START_TIME, DEFAULT_END_TIME, DEFAULT_BREAK_MINUTES, DEFAULT_SIDE_JOB_MINUTES, DEFAULT_START_INTERRUPTION, DEFAULT_END_INTERRUPTION, DEFAULT_INTERRUPTION


#勤怠入力ページのメイン処理。
#セッション初期化、データ取得、フォーム表示を行う。


PAGE_NAME = "input"
session_state_list = ["last_payload", "saved", "deleted", "error"]

# ページ遷移時にセッションステートを初期化する
init_session_state(PAGE_NAME, session_state_list)

st.title("勤怠入力")
record_date: date = st.date_input("対象日付", date.today())

# 勤怠データをAPIから取得
data = fetch_attendance_data(record_date)
if data is None:
    st.error("データ取得に失敗したため、入力欄を表示できません。")


# 取得したデータが空でない場合は、各値を設定
if data:
    start_time = parse_time_str(data.get("start_time")) if data.get("start_time") else DEFAULT_START_TIME
    end_time = parse_time_str(data.get("end_time")) if data.get("end_time") else DEFAULT_END_TIME
    break_minutes = int(data.get("break_minutes", DEFAULT_BREAK_MINUTES))
    interruptions = data.get("interruptions", DEFAULT_INTERRUPTION)
    side_job_minutes = int(data.get("side_job_minutes", DEFAULT_SIDE_JOB_MINUTES))
    updated_at = data.get("updated_at")
    comment = data.get("comment", "")
    st.markdown("🟢 登録済み")
# 取得したデータが空の場合は、初期値を設定
else:
    st.info("この日付のデータはありません。新規入力できます。")
    start_time = DEFAULT_START_TIME
    end_time = DEFAULT_END_TIME
    break_minutes = DEFAULT_BREAK_MINUTES
    interruptions = DEFAULT_INTERRUPTION
    side_job_minutes = DEFAULT_SIDE_JOB_MINUTES
    updated_at = None
    comment = ""  # ← ここを追加
    st.markdown("🔴 未登録")

# 最終更新日時を表示
show_last_updated(updated_at)

# 勤怠入力フォームを表示
# 取得したデータが空でない場合は、各値を設定
if None not in (start_time, end_time, break_minutes, interruptions, side_job_minutes, comment):
    show_attendance_form(
        record_date, start_time, end_time, break_minutes, interruptions, side_job_minutes, comment
    )
else:
    st.error("データ取得に失敗したため、入力欄を表示できません。")

