import streamlit as st
import requests
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from common import parse_time_str, render_calendar, init_session_state, fetch_monthly_attendance, render_edit_blocks
from settings import API_URL, DEFAULT_START_TIME, DEFAULT_END_TIME, DEFAULT_BREAK_MINUTES, DEFAULT_INTERRUPTION, DEFAULT_START_INTERRUPTION, DEFAULT_END_INTERRUPTION, DEFAULT_SIDE_JOB_MINUTES
from typing import Any, Dict, List, Optional
import plotly.graph_objects as go
import numpy as np
import pandas as pd

# ページ名を定義
PAGE_NAME = "edit"
session_state_list = ["last_payload", "saved", "deleted", "error"]

# ページ遷移時にセッションステートを初期化する
init_session_state(PAGE_NAME, session_state_list)

st.title("勤怠確認・編集")


# 対象月選択（初期値：今月1日）
today = date.today()
default_month = date(today.year, today.month, 1)
selected_month = st.date_input("対象月（Streamlitの仕様上日付を選択）", value=default_month)

# 表示だけ「YYYY-MM」にする
st.markdown(f"## 対象月: {selected_month.strftime('%Y-%m')}")


month_str = selected_month.strftime("%Y-%m")
records = fetch_monthly_attendance(month_str)

# 日付の昇順（古い→新しい）でソート
records = sorted(records, key=lambda r: r["date"])

# --- 集計用変数 ---
work_total = timedelta()
break_total = 0
interrupt_total = timedelta()
side_job_total = 0

for data in records:
    # 勤務合計
    if data.get("start_time") and data.get("end_time"):
        s = parse_time_str(data.get("start_time"))
        e = parse_time_str(data.get("end_time"))
        dt_s = datetime.combine(date.today(), s)
        dt_e = datetime.combine(date.today(), e)
        work_total += (dt_e - dt_s)

    # 休憩合計
    break_total += int(data.get("break_minutes", 0))

    # 中断合計
    interruptions = data.get("interruptions", 0)
    for it in interruptions:
        its = parse_time_str(it.get("start"))
        ite = parse_time_str(it.get("end"))
        if its and ite:
            dt_its = datetime.combine(date.today(), its)
            dt_ite = datetime.combine(date.today(), ite)
            interrupt_total += (dt_ite - dt_its)

    # 副業合計
    side_job_total += int(data.get("side_job_minutes", DEFAULT_SIDE_JOB_MINUTES))
# --- 集計値の計算 ---
work_total_hours = work_total.total_seconds() / 3600
break_total_hours = break_total / 60
interrupt_total_hours = interrupt_total.total_seconds() / 3600
side_job_total_hours = side_job_total / 60

gross_total_hours = work_total_hours + side_job_total_hours  # 総勤務時間
actual_work_hours = work_total_hours - break_total_hours - interrupt_total_hours  # 実働時間

# --- 勤務日数の計算 ---
work_days = len([
    r for r in records
    if r.get("start_time") and r.get("end_time")
])

# --- 集計表の表示 ---
st.markdown("## 月集計")
st.table({
    "項目": [
        "勤務日数",
        "総勤務時間：勤務合計と副業合計の総合計", 
        "勤務合計：開始と終了からのみ算出した時間", 
        "実働時間：勤務合計から休憩と中断を引いた時間",
        "休憩合計：休憩時間の合計", 
        "中断合計：中断時間の合計", 
        "副業合計：副業時間の合計",
    ],
    "値": [
        f"{work_days} 日",
        f"{gross_total_hours:.2f} h",         # 総勤務時間
        f"{work_total_hours:.2f} h",           # 勤務合計
        f"{actual_work_hours:.2f} h",          # 実働時間
        f"{break_total_hours:.2f} h",          # 休憩合計
        f"{interrupt_total_hours:.2f} h",      # 中断合計
        f"{side_job_total_hours:.2f} h",       # 副業合計
    ]
})

# --- カレンダーの表示 ---
st.markdown("## 入力一覧（リンク付き）")
# 入力ありの日付セット
input_dates_set = set(pd.to_datetime([
    r["date"] for r in records
    if r.get("start_time") or r.get("end_time") or r.get("side_job_minutes", 0) > 0
]).date)
table_html = render_calendar(selected_month.year, selected_month.month, input_dates_set)
st.markdown(table_html, unsafe_allow_html=True)

# --- 勤怠データの表示 ---
st.markdown("## 編集・削除")
render_edit_blocks(records)

# リロード後もpayloadを表示
if "last_payload" in st.session_state:
    st.write("直近の送信データ（payload）:", st.session_state["last_payload"])