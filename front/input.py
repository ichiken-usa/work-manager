import streamlit as st
import requests
from datetime import datetime, time, date
from typing import Any, Dict, List, Optional
from common import parse_time_str


API_URL: str = "http://back:8000/api"

DEFAULT_START_TIME: time = time(8, 30)
DEFAULT_END_TIME: time = time(17, 30)
DEFAULT_BREAK_MINUTES: int = 60
DEFAULT_INTERRUPTION: List[Dict[str, str]] = []
DEFAULT_START_INTERRUPTION = "17:45"
DEFAULT_END_INTERRUPTION = "19:00"
DEFAULT_SIDE_JOB_MINUTES: int = 0


st.title("勤怠入力")

record_date: date = st.date_input("対象日付", date.today())

data: Dict[str, Any] = {}
updated_at: Optional[str] = None
start_time: Optional[time] = None
end_time: Optional[time] = None
break_minutes: Optional[int] = None
interruptions: Optional[List[Dict[str, str]]] = None
side_job_minutes: Optional[int] = None

try:
    res = requests.get(f"{API_URL}/attendance/{record_date.isoformat()}")
    if res.status_code == 200:
        data = res.json()
        start_time = parse_time_str(data.get("start_time")) if data.get("start_time") else DEFAULT_START_TIME
        end_time = parse_time_str(data.get("end_time")) if data.get("end_time") else DEFAULT_END_TIME
        break_minutes = int(data.get("break_minutes", DEFAULT_BREAK_MINUTES))
        interruptions = data.get("interruptions", DEFAULT_INTERRUPTION)
        side_job_minutes = int(data.get("side_job_minutes", DEFAULT_SIDE_JOB_MINUTES))
        updated_at = data.get("updated_at")
        st.markdown("🟢 登録済み")
    elif res.status_code == 404:
        st.info("この日付のデータはありません。新規入力できます。")
        start_time = DEFAULT_START_TIME
        end_time = DEFAULT_END_TIME
        break_minutes = DEFAULT_BREAK_MINUTES
        interruptions = DEFAULT_INTERRUPTION
        side_job_minutes = DEFAULT_SIDE_JOB_MINUTES
        st.markdown("🔴 未登録")
    else:
        st.warning(f"データ取得失敗: {res.status_code}")
        start_time = None
        end_time = None
        break_minutes = None
        interruptions = None
        side_job_minutes = None
except Exception as e:
    st.error(f"取得失敗: {e}")
    start_time = None
    end_time = None
    break_minutes = None
    interruptions = None
    side_job_minutes = None

if updated_at:
    try:
        dt = datetime.fromisoformat(updated_at)
        st.info(f"最終更新日時: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception:
        st.info(f"最終更新日時: {updated_at}")

if None not in (start_time, end_time, break_minutes, interruptions, side_job_minutes):
    col1, col2 = st.columns(2)
    with col1:
        start_time = st.time_input("開始時刻", value=start_time, key="start_time_input")
    with col2:
        end_time = st.time_input("終了時刻", value=end_time, key="end_time_input")

    # 開始・終了時刻のバリデーション
    if start_time >= end_time:
        st.error("開始時刻は終了時刻より早くしてください。")
        can_save = False
    else:
        can_save = True

    break_minutes = st.number_input(
        "休憩時間（分）",
        min_value=0,
        step=1,
        value=int(break_minutes) if break_minutes is not None else DEFAULT_BREAK_MINUTES
    )

    st.markdown("### その他")
    new_interruptions: List[Dict[str, str]] = []
    num_interrupts: int = st.number_input("中断回数", min_value=0, step=1, value=len(interruptions))

    interruption_valid = True  # 中断バリデーション用フラグ

    for i in range(num_interrupts):
        col1, col2 = st.columns(2)
        default_start: str = interruptions[i]['start'] if i < len(interruptions) else DEFAULT_START_INTERRUPTION
        default_end: str = interruptions[i]['end'] if i < len(interruptions) else DEFAULT_END_INTERRUPTION
        with col1:
            istart: time = st.time_input(f"中断 {i+1} 開始", value=parse_time_str(default_start), key=f"interrupt_start_{i}")
        with col2:
            iend: time = st.time_input(f"中断 {i+1} 終了", value=parse_time_str(default_end), key=f"interrupt_end_{i}")
        new_interruptions.append({"start": istart.strftime("%H:%M"), "end": iend.strftime("%H:%M")})

        # 中断時間のバリデーション
        if istart >= iend:
            st.error(f"中断{i+1}の開始時刻は終了時刻より早くしてください。")
            interruption_valid = False

    side_job_minutes = st.number_input(
        "副業時間（分）",
        min_value=0,
        step=15,
        value=int(side_job_minutes)
    )

    # 保存ボタンの有効判定に interruption_valid も加える
    if st.button("保存") and can_save and interruption_valid:
        payload: Dict[str, Any] = {
            "date": record_date.isoformat(),
            "start_time": start_time.strftime("%H:%M"),
            "end_time": end_time.strftime("%H:%M"),
            "break_minutes": break_minutes,
            "interruptions": new_interruptions,
            "side_job_minutes": side_job_minutes
        }
        st.session_state["last_payload"] = payload
        res = requests.post(f"{API_URL}/attendance/{record_date.isoformat()}", json=payload)
        if res.status_code == 200:
            st.session_state["saved"] = True
            st.rerun()
        else:
            st.error(f"保存に失敗しました: {res.text}")

    if st.session_state.get("saved", False):
        st.success("保存しました")
        st.session_state["saved"] = False

    # リロード後もpayloadを表示
    if "last_payload" in st.session_state:
        st.write("直近の送信データ（payload）:", st.session_state["last_payload"])


else:
    st.error("データ取得に失敗したため、入力欄を表示できません。")