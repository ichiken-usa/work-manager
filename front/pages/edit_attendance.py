import streamlit as st
from datetime import datetime, date, timedelta
import pandas as pd

from modules.api_client import fetch_monthly_attendance, fetch_aggregate_attendance
from modules.ui_components import render_calendar, render_edit_blocks
from modules.session import init_session_state



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


# --- 集計 ---
agg = fetch_aggregate_attendance(month_str)

work_total_hours = agg["work_total_hours"]
break_total_hours = agg["break_total_hours"]
interrupt_total_hours = agg["interrupt_total_hours"]
side_job_total_hours = agg["side_job_total_hours"]
gross_total_hours = agg["gross_total_hours"]
actual_work_hours = agg["actual_work_hours"]
work_days = agg["work_days"]

# --- 集計表の表示 ---
st.markdown("## 月集計")
st.table({
    "項目": [
        "総日数:入力のある全日数",
        "総勤務時間：勤務合計と副業合計の総合計", 
        "勤務日数：勤務時間登録がある日数",
        "勤務合計：開始と終了からのみ算出した時間", 
        "実働時間：勤務合計から休憩と中断を引いた時間",
        "休憩合計：休憩時間の合計", 
        "中断合計：中断時間の合計", 
        "副業合計：副業時間の合計",
    ],
    "値": [
        f"{agg['gross_days']} 日",
        f"{agg['gross_total_hours']:.2f} h",
        f"{agg['work_days']} 日",
        f"{agg['work_total_hours']:.2f} h",
        f"{agg['actual_work_hours']:.2f} h",
        f"{agg['break_total_hours']:.2f} h",
        f"{agg['interrupt_total_hours']:.2f} h",
        f"{agg['side_job_total_hours']:.2f} h",
    ]
})

# --- 勤怠データの取得 ---
records = fetch_monthly_attendance(month_str)

# 日付の昇順（古い→新しい）でソート
records = sorted(records, key=lambda r: r["date"])

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