import streamlit as st
import requests
from datetime import datetime, time, date
from typing import Any, Dict, List, Optional
from common import parse_time_str, save_attendance
from settings import API_URL, DEFAULT_START_TIME, DEFAULT_END_TIME, DEFAULT_BREAK_MINUTES, DEFAULT_INTERRUPTION, DEFAULT_START_INTERRUPTION, DEFAULT_END_INTERRUPTION, DEFAULT_SIDE_JOB_MINUTES

PAGE_NAME = "input"

def init_session_state():
    """
    ページ遷移時にセッションステートを初期化する。
    他ページから遷移してきた場合、last_payload, saved, deletedをクリアする。
    """
    if st.session_state.get("current_page") != PAGE_NAME:
        st.session_state["current_page"] = PAGE_NAME
        for key in ["last_payload", "saved", "deleted"]:
            if key in st.session_state:
                del st.session_state[key]

def fetch_attendance_data(record_date: date) -> Optional[Dict[str, Any]]:
    """
    指定した日付の勤怠データをAPIから取得する。

    Args:
        record_date (date): 取得対象日付

    Returns:
        dict or None: 勤怠データ（存在しない場合は空dict、失敗時はNone）
    """
    try:
        res = requests.get(f"{API_URL}/attendance/{record_date.isoformat()}")
        if res.status_code == 200:
            return res.json()
        elif res.status_code == 404:
            return {}
        else:
            st.warning(f"データ取得失敗: {res.status_code}")
            return None
    except Exception as e:
        st.error(f"取得失敗: {e}")
        return None

def show_last_updated(updated_at: Optional[str]):
    """
    最終更新日時を表示する。

    Args:
        updated_at (str or None): ISO形式の日時文字列
    """
    if updated_at:
        try:
            dt = datetime.fromisoformat(updated_at)
            st.info(f"最終更新日時: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception:
            st.info(f"最終更新日時: {updated_at}")

def show_attendance_form(
    record_date: date,
    start_time: time,
    end_time: time,
    break_minutes: int,
    interruptions: List[Dict[str, str]],
    side_job_minutes: int
):
    """
    勤怠入力フォームを表示し、保存処理を行う。
    チェックボックスOFF時は開始・終了時刻、休憩時間の入力不可。
    """
    start_time_enabled = st.checkbox("時刻を入力する", value=bool(start_time))

    col1, col2 = st.columns(2)

    with col1:
        start_time_val = st.time_input(
            "開始時刻",
            value=start_time if start_time else time(0, 0),
            key="start_time_input",
            disabled=not start_time_enabled
        )
    with col2:
        end_time_val = st.time_input(
            "終了時刻",
            value=end_time if end_time else time(0, 0),
            key="end_time_input",
            disabled=not start_time_enabled
        )

    # 入力有無で値を決定
    start_time_final = start_time_val if start_time_enabled else None
    end_time_final = end_time_val if start_time_enabled else None

    can_save = True
    if start_time_enabled:
        if start_time_final > end_time_final:
            st.error("開始時刻は終了時刻より早くしてください。")
            can_save = False

    break_minutes = st.number_input(
        "休憩時間（分）",
        min_value=0,
        step=15,
        value=int(break_minutes) if break_minutes is not None else DEFAULT_BREAK_MINUTES,
        disabled=not start_time_enabled
    )

    st.markdown("### その他")
    new_interruptions: List[Dict[str, str]] = []
    num_interrupts: int = st.number_input("中断回数", min_value=0, step=1, value=len(interruptions))

    interruption_valid = True
    for i in range(num_interrupts):
        col1, col2 = st.columns(2)
        default_start: str = interruptions[i]['start'] if i < len(interruptions) else DEFAULT_START_INTERRUPTION
        default_end: str = interruptions[i]['end'] if i < len(interruptions) else DEFAULT_END_INTERRUPTION
        with col1:
            istart: time = st.time_input(f"中断 {i+1} 開始", value=parse_time_str(default_start), key=f"interrupt_start_{i}")
        with col2:
            iend: time = st.time_input(f"中断 {i+1} 終了", value=parse_time_str(default_end), key=f"interrupt_end_{i}")
        new_interruptions.append({"start": istart.strftime("%H:%M"), "end": iend.strftime("%H:%M")})

        if istart >= iend:
            st.error(f"中断{i+1}の開始時刻は終了時刻より早くしてください。")
            interruption_valid = False

    side_job_minutes = st.number_input(
        "副業時間（分）",
        min_value=0,
        step=15,
        value=int(side_job_minutes)
    )

    if st.button("保存") and can_save and interruption_valid:
        payload: Dict[str, Any] = {
            "date": record_date.isoformat(),
            "start_time": start_time_final.strftime("%H:%M") if start_time_final else "",
            "end_time": end_time_final.strftime("%H:%M") if end_time_final else "",
            "break_minutes": break_minutes if start_time_enabled else 0,
            "interruptions": new_interruptions,
            "side_job_minutes": side_job_minutes
        }
        st.session_state["last_payload"] = payload
        success = save_attendance(record_date.isoformat(), payload, API_URL)
        if success:
            st.session_state["saved"] = True
            st.rerun()

    if "last_payload" in st.session_state:
        st.write("直近の送信データ（payload）:", st.session_state["last_payload"])

def main():
    """
    勤怠入力ページのメイン処理。
    セッション初期化、データ取得、フォーム表示を行う。
    """
    init_session_state()
    message = ''

    st.title("勤怠入力")
    record_date: date = st.date_input("対象日付", date.today())

    data = fetch_attendance_data(record_date)
    if data is None:
        st.error("データ取得に失敗したため、入力欄を表示できません。")
        return

    if data:
        start_time = parse_time_str(data.get("start_time")) if data.get("start_time") else DEFAULT_START_TIME
        end_time = parse_time_str(data.get("end_time")) if data.get("end_time") else DEFAULT_END_TIME
        break_minutes = int(data.get("break_minutes", DEFAULT_BREAK_MINUTES))
        interruptions = data.get("interruptions", DEFAULT_INTERRUPTION)
        side_job_minutes = int(data.get("side_job_minutes", DEFAULT_SIDE_JOB_MINUTES))
        updated_at = data.get("updated_at")
        st.markdown("🟢 登録済み")
    else:
        st.info("この日付のデータはありません。新規入力できます。")
        start_time = DEFAULT_START_TIME
        end_time = DEFAULT_END_TIME
        break_minutes = DEFAULT_BREAK_MINUTES
        interruptions = DEFAULT_INTERRUPTION
        side_job_minutes = DEFAULT_SIDE_JOB_MINUTES
        updated_at = None
        st.markdown("🔴 未登録")

    show_last_updated(updated_at)

    if None not in (start_time, end_time, break_minutes, interruptions, side_job_minutes):
        show_attendance_form(
            record_date, start_time, end_time, break_minutes, interruptions, side_job_minutes
        )
    else:
        st.error("データ取得に失敗したため、入力欄を表示できません。")

if __name__ == "__main__" or True:
    main()