import streamlit as st
import requests
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from common import parse_time_str, serialize_interruptions
from settings import API_URL, DEFAULT_START_TIME, DEFAULT_END_TIME, DEFAULT_BREAK_MINUTES, DEFAULT_INTERRUPTION, DEFAULT_START_INTERRUPTION, DEFAULT_END_INTERRUPTION, DEFAULT_SIDE_JOB_MINUTES
from typing import Any, Dict, List, Optional
import plotly.graph_objects as go
import numpy as np
import calendar
import pandas as pd


# ページ名を定義
PAGE_NAME = "edit"

# セッションステートの初期化
if st.session_state.get("current_page") != PAGE_NAME:
    st.session_state["current_page"] = PAGE_NAME

    if "last_payload" in st.session_state:
        del st.session_state["last_payload"]
    if "saved" in st.session_state:
        del st.session_state["saved"]
    if "deleted" in st.session_state:
        del st.session_state["deleted"]


st.title("勤怠確認・編集")


# 対象月選択（初期値：今月1日）
today = date.today()
default_month = date(today.year, today.month, 1)
selected_month = st.date_input("対象月（Streamlitの仕様上日付を選択）", value=default_month)

# 表示だけ「YYYY-MM」にする
st.markdown(f"## 対象月: {selected_month.strftime('%Y-%m')}")


month_str = selected_month.strftime("%Y-%m")

# 勤怠データ取得
#@st.cache_data
def fetch_monthly_attendance(month_str):
    try:
        res = requests.get(f"{API_URL}/attendance/month/{month_str}")
        if res.status_code == 200:
            print(f'{API_URL}/attendance/month/{month_str} : {res.json()}')
            return res.json()
    except Exception as e:
        st.error(f"取得失敗: {e}")
    return []

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

# カレンダー情報の作成
year = selected_month.year
month = selected_month.month
month_range = calendar.monthrange(year, month)[1]
days = [date(year, month, d) for d in range(1, month_range + 1)]

# 入力ありの日付セット
input_dates_set = set(pd.to_datetime([
    r["date"] for r in records
    if r.get("start_time") or r.get("end_time") or r.get("side_job_minutes", 0) > 0
]).date)

# 曜日ラベル（日曜スタート）
weekday_labels = ["日", "月", "火", "水", "木", "金", "土"]

# カレンダー行列作成（週ごとにリスト化、各週は曜日順、日曜スタート）
calendar_matrix = []
week = [None] * 7  # 1週分の空リスト
for d in days:
    wd = (d.weekday() + 1) % 7  # 0=日, ..., 6=土
    if wd == 0 and any(week):  # 新しい週
        calendar_matrix.append(week)
        week = [None] * 7
    week[wd] = d
calendar_matrix.append(week)  # 最後の週

# 1週目の前に日付がない曜日をNoneで埋める
first_week = calendar_matrix[0]
for i in range(7):
    if first_week[i] is None:
        continue
    else:
        break
for j in range(i):
    first_week[j] = None

# 最終週の後ろもNoneで埋める
last_week = calendar_matrix[-1]
for i in range(7):
    if last_week[i] is None:
        last_week[i] = None

# HTMLテーブル生成
table_html = "<table style='border-collapse:collapse;text-align:center;'>"
# ヘッダー（曜日）
table_html += "<tr><th></th>"
for label in weekday_labels:
    table_html += f"<th>{label}</th>"
table_html += "</tr>"
# カレンダーHTML生成部（cell部分のみ修正）
for w, week in enumerate(calendar_matrix):
    table_html += f"<tr><th>{w+1}週</th>"
    for d in week:
        if d is None:
            cell = ""
        elif d in input_dates_set:
            # アンカーリンク付き
            cell = f'<a href="#edit-{d.isoformat()}"><span style="background-color:#4F8DFD;color:white;padding:2px 6px;border-radius:4px">{d.day}</span></a>'
        else:
            cell = str(d.day)
        table_html += f'<td style="border:1px solid #ccc;min-width:32px;height:32px">{cell}</td>'
    table_html += "</tr>"

st.markdown(table_html, unsafe_allow_html=True)

# --- 勤怠データの表示 ---
st.markdown("## 編集・削除")
for data in records:
    record_date = data["date"]
    interruptions = data.get("interruptions", DEFAULT_INTERRUPTION)
    comment = data.get("comment", "")
    st.markdown(f'<a id="edit-{record_date}"></a>', unsafe_allow_html=True)

    with st.container():
        st.markdown(f"### {record_date}")

        col1, col2 = st.columns(2)

        with col1:
            start_time = st.time_input(
                "開始",
                value=parse_time_str(data.get("start_time")) if data.get("start_time") else None,
                key=f"{record_date}_start_time_input",
            )
            end_time = st.time_input(
                "終了",
                value=parse_time_str(data.get("end_time")) if data.get("end_time") else None,
                key=f"{record_date}_end_time_input",
            )
            break_minutes = st.number_input(
                "休憩(分)",
                min_value=0,
                step=1,
                value=int(data.get("break_minutes", None)),
                key=f"{record_date}_break_minutes_input",
            )

        with col2:
            side_job_minutes = st.number_input(
                "副業(分)",
                min_value=0,
                step=15,
                value=int(data.get("side_job_minutes", DEFAULT_SIDE_JOB_MINUTES)),
                key=f"{record_date}_side_job_minutes_input",
            )
            st.markdown("**中断時間**")
            if interruptions:
                st.markdown("<br>".join([f'{i["start"]}-{i["end"]}' for i in interruptions]), unsafe_allow_html=True)
            else:
                st.markdown("None")

            # コメント欄を追加
            comment_val = st.text_area(
                "コメント",
                value=comment,
                key=f"{record_date}_comment_input"
            )

            col_save, col_delete = st.columns(2)
            with col_save:
                if st.button("SAVE", key=f"{record_date}_save"):
                    payload: Dict[str, Any] = {
                        "date": record_date,
                        "start_time": start_time.strftime("%H:%M") if start_time else "",
                        "end_time": end_time.strftime("%H:%M") if end_time else "",
                        "break_minutes": break_minutes,
                        "interruptions": interruptions,
                        "side_job_minutes": side_job_minutes,
                        "comment": comment_val
                    }
                    print(f'POST Data: {payload}')
                    st.session_state["last_payload"] = payload
                    res = requests.post(f"{API_URL}/attendance/{record_date}", json=payload)
                    if res.status_code == 200:
                        st.session_state["saved"] = True
                        st.rerun()
                    else:
                        st.error(f"保存に失敗: {res.text}")
            with col_delete:
                if st.button("DELETE", key=f"{record_date}_delete"):
                    st.session_state["last_payload"] = None
                    res = requests.delete(f"{API_URL}/attendance/{record_date}")
                    if res.status_code == 200:
                        st.session_state['deleted'] = True
                        st.rerun()
                    else:
                        st.error(f"削除に失敗: {res.text}")

        if st.session_state.get("saved", False):
            st.success("保存しました")
            st.session_state["saved"] = False

        st.markdown("---")



# リロード後もpayloadを表示
if "last_payload" in st.session_state:
    st.write("直近の送信データ（payload）:", st.session_state["last_payload"])