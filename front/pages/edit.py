import streamlit as st
import requests
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from common import parse_time_str, serialize_interruptions
from settings import API_URL, DEFAULT_START_TIME, DEFAULT_END_TIME, DEFAULT_BREAK_MINUTES, DEFAULT_INTERRUPTION, DEFAULT_START_INTERRUPTION, DEFAULT_END_INTERRUPTION, DEFAULT_SIDE_JOB_MINUTES
from typing import Any, Dict, List, Optional

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
st.markdown(f"### 対象月: {selected_month.strftime('%Y-%m')}")


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
    s = parse_time_str(data.get("start_time")) if data.get("start_time") else DEFAULT_START_TIME
    e = parse_time_str(data.get("end_time")) if data.get("end_time") else DEFAULT_END_TIME
    dt_s = datetime.combine(date.today(), s)
    dt_e = datetime.combine(date.today(), e)
    work_total += (dt_e - dt_s)

    # 休憩合計
    break_total += int(data.get("break_minutes", DEFAULT_BREAK_MINUTES))

    # 中断合計
    interruptions = data.get("interruptions", DEFAULT_INTERRUPTION)
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
for data in records:
    record_date = data["date"]
    interruptions = data.get("interruptions", DEFAULT_INTERRUPTION)

    with st.container():
        st.markdown(f"### {record_date}")

        col1, col2 = st.columns(2)

        with col1:
            start_time = st.time_input(
                "開始",
                value=parse_time_str(data.get("start_time")) if data.get("start_time") else DEFAULT_START_TIME,
                key=f"{record_date}_start_time_input",
            )
            end_time = st.time_input(
                "終了",
                value=parse_time_str(data.get("end_time")) if data.get("end_time") else DEFAULT_END_TIME,
                key=f"{record_date}_end_time_input",
            )
            break_minutes = st.number_input(
                "休憩(分)",
                min_value=0,
                step=1,
                value=int(data.get("break_minutes", DEFAULT_BREAK_MINUTES)),
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

            col_save, col_delete = st.columns(2)
            with col_save:
                if st.button("SAVE", key=f"{record_date}_save"):
                    payload: Dict[str, Any] = {
                        "date": record_date,
                        "start_time": start_time.strftime("%H:%M") if start_time else "",
                        "end_time": end_time.strftime("%H:%M") if end_time else "",
                        "break_minutes": break_minutes,
                        "interruptions": interruptions,
                        "side_job_minutes": side_job_minutes
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