# Streamlit UI部品・描画系
from datetime import date, datetime, time
from typing import Any, Dict, List, Optional
import requests
import streamlit as st

from modules.time_utils import parse_time_str
from modules.api_client import save_attendance
from settings import (
    API_URL,
    DEFAULT_START_TIME,
    DEFAULT_END_TIME,
    DEFAULT_BREAK_MINUTES,
    DEFAULT_INTERRUPTION,
    DEFAULT_START_INTERRUPTION,
    DEFAULT_END_INTERRUPTION,
    DEFAULT_SIDE_JOB_MINUTES,
)

def show_attendance_form(
    record_date: date,
    start_time: time,
    end_time: time,
    break_minutes: int,
    interruptions: List[Dict[str, str]],
    side_job_minutes: int,
    comment: Optional[str] = None
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

    # コメント入力欄を追加
    comment = st.text_area("コメント", value=comment, key="comment_input")

    # 入力値を返す
    return {
        "start_time": start_time_final,
        "end_time": end_time_final,
        "break_minutes": break_minutes if start_time_enabled else 0,
        "interruptions": new_interruptions,
        "side_job_minutes": side_job_minutes,
        "comment": comment,
        "can_save": can_save and interruption_valid,
        "start_time_enabled": start_time_enabled
    }

def render_calendar(year, month, input_dates_set):
    """日曜始まり・週×曜日のカレンダーHTMLを返す"""
    import calendar

    # カレンダー情報の作成
    month_range = calendar.monthrange(year, month)[1]
    days = [date(year, month, d) for d in range(1, month_range + 1)]

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
    # カレンダーHTML生成部
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
    table_html += "</table>"
    return table_html

def render_calendar_only(year, month, input_dates_set, select_key="selected_date"):
    """
    日曜始まり・週×曜日のカレンダーHTMLを返す（表示のみ、日付選択機能なし）。
    """
    import calendar
    from datetime import date

    # カレンダー情報の作成
    month_range = calendar.monthrange(year, month)[1]
    days = [date(year, month, d) for d in range(1, month_range + 1)]

    # 曜日ラベル（日曜スタート）
    weekday_labels = ["日", "月", "火", "水", "木", "金", "土"]

    # カレンダー行列作成
    calendar_matrix = []
    week = [None] * 7
    for d in days:
        wd = (d.weekday() + 1) % 7  # 0=日, ..., 6=土
        if wd == 0 and any(week):
            calendar_matrix.append(week)
            week = [None] * 7
        week[wd] = d
    calendar_matrix.append(week)

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

    # HTMLテーブル生成（表示のみ）
    table_html = "<table style='border-collapse:collapse;text-align:center;'>"
    table_html += "<tr><th></th>"
    for label in weekday_labels:
        table_html += f"<th>{label}</th>"
    table_html += "</tr>"
    for w, week in enumerate(calendar_matrix):
        table_html += f"<tr><th>{w+1}週</th>"
        for d in week:
            if d is None:
                cell = ""
            else:
                if d in input_dates_set:
                    cell = f'<span style="background-color:#4F8DFD;color:white;padding:2px 6px;border-radius:4px">{d.day}</span>'
                else:
                    cell = str(d.day)
            table_html += f'<td style="border:1px solid #ccc;min-width:32px;height:32px">{cell}</td>'
        table_html += "</tr>"
    table_html += "</table>"
    st.markdown(table_html, unsafe_allow_html=True)


def render_edit_blocks(records):
    """編集・削除ブロックを表示"""
    message = None
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
                            #st.rerun()
                        else:
                            st.session_state["error"] = True
                            message = res.text
                with col_delete:
                    if st.button("DELETE", key=f"{record_date}_delete"):
                        st.session_state["last_payload"] = None
                        res = requests.delete(f"{API_URL}/attendance/{record_date}")
                        if res.status_code == 200:
                            st.session_state['deleted'] = True
                            st.rerun()
                        else:
                            st.error(f"削除に失敗: {res.text}")

            if st.session_state.get("saved"):
                st.success("保存しました。")
                st.session_state["saved"] = False
            if st.session_state.get("error"):
                st.error(f"保存に失敗しました: {message}")
                st.session_state["error"] = False
            st.markdown("---")


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
