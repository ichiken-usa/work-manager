from datetime import datetime, time, date
from typing import Any, Dict, List, Optional
import requests
import streamlit as st
from settings import API_URL, DEFAULT_START_TIME, DEFAULT_END_TIME, DEFAULT_BREAK_MINUTES, DEFAULT_INTERRUPTION, DEFAULT_START_INTERRUPTION, DEFAULT_END_INTERRUPTION, DEFAULT_SIDE_JOB_MINUTES

def parse_time_str(tstr: Optional[str]) -> time:
    """"HH:MM"形式の文字列をtime型に変換。失敗時は00:00を返す。"""
    if not tstr:
        return time(0, 0)
    try:
        return datetime.strptime(tstr, "%H:%M").time()
    except Exception:
        return time(0, 0)
    
# interruptionsを文字列（"HH:MM"）に変換
def serialize_interruptions(inter_list):
    result = []
    for i in inter_list:
        result.append({
            "start": i["start"].strftime("%H:%M") if isinstance(i["start"], datetime.time) else i["start"],
            "end": i["end"].strftime("%H:%M") if isinstance(i["end"], datetime.time) else i["end"],
        })
    return result


def save_attendance(record_date, payload: Dict[str, Any], api_url: str) -> bool:
    """
    勤怠データをAPIに保存する共通関数。

    Args:
        record_date: 対象日付（date型またはisoformat文字列）
        payload (dict): 保存するデータ
        api_url (str): APIのベースURL

    Returns:
        bool: 保存成功時はTrue、失敗時はFalse
    """
    try:
        res = requests.post(f"{api_url}/attendance/{record_date}", json=payload)
        if res.status_code == 200:
            return True
        else:
            st.error(f"保存に失敗しました: {res.text}")
            return False
    except Exception as e:
        st.error(f"保存時に例外が発生しました: {e}")
        return False
    

def init_session_state(PAGE_NAME: str, session_state_list: List[str]):
    """
    ページ遷移時にセッションステートを初期化する。
    他ページから遷移してきた場合、last_payload, saved, deletedをクリアする。
    """
    if st.session_state.get("current_page") != PAGE_NAME:
        st.session_state["current_page"] = PAGE_NAME
        for key in session_state_list:
            if key in st.session_state:
                del st.session_state[key]

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
