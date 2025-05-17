import streamlit as st
import requests
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

def parse_time_str(tstr):
    try:
        # ミリ秒付き
        return datetime.strptime(tstr, "%H:%M:%S.%f").time()
    except ValueError:
        # ミリ秒なし
        return datetime.strptime(tstr, "%H:%M:%S").time()
    
# interruptionsを文字列（"HH:MM"）に変換
def serialize_interruptions(inter_list):
    result = []
    for i in inter_list:
        result.append({
            "start": i["start"].strftime("%H:%M") if isinstance(i["start"], datetime.time) else i["start"],
            "end": i["end"].strftime("%H:%M") if isinstance(i["end"], datetime.time) else i["end"],
        })
    return result


    
API_URL = "http://back:8000/api"

st.title("勤怠確認・編集")

# 対象月選択（初期値：今月1日）
today = date.today()
default_month = date(today.year, today.month, 1)
selected_month = st.date_input("対象月（Streamlitの仕様上日付を選択）", value=default_month)

# 表示だけ「YYYY-MM」にする
st.markdown(f"### 対象月: {selected_month.strftime('%Y-%m')}")

month_str = selected_month.strftime("%Y-%m")

# 勤怠データ取得
@st.cache_data
def fetch_monthly_attendance(month_str):
    try:
        res = requests.get(f"{API_URL}/attendance/month/{month_str}")
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"取得失敗: {e}")
    return []

records = fetch_monthly_attendance(month_str)

# 日付の昇順（古い→新しい）でソート
records = sorted(records, key=lambda r: r["date"])

if not records:
    st.warning("データがありません。")
else:
    # ヘッダー
    header_cols = st.columns([2, 3, 3, 2, 2, 2, 2])
    headers = ["日付", "開始時刻", "終了時刻", "休憩（分）", "副業（分）", "中断時間", "保存"]
    for col, h in zip(header_cols, headers):
        col.markdown(f"**{h}**")

    for rec in records:
        date_str = rec["date"]
        row_cols = st.columns([2, 3, 3, 2, 2, 2, 2])

        # 日付
        row_cols[0].markdown(f"{date_str}")

        # 開始・終了時刻（秒を除去して表示）
        start_val = (rec.get("start_time") or "")[:5]
        end_val = (rec.get("end_time") or "")[:5]
        start = row_cols[1].time_input("", value=start_val, key=f"{date_str}_start")
        end = row_cols[2].time_input("", value=end_val, key=f"{date_str}_end")

        # 休憩時間
        break_m = row_cols[3].number_input(
            "", min_value=0, value=int(rec.get("break_minutes") or 0), step=1, key=f"{date_str}_break"
        )

        # 副業時間
        side_job = row_cols[4].number_input(
            "", min_value=0, value=int(rec.get("side_job_minutes") or 0), step=15, key=f"{date_str}_side"
        )

        # 中断時間（簡易表示：件数のみ）
        inter_list = rec.get("interruptions") or []
        inter_disp = " / ".join([f"{i['start']}-{i['end']}" for i in inter_list]) if inter_list else "-"
        row_cols[5].markdown(inter_disp)

        # 保存ボタン
        # 保存ボタンの処理内で
        if row_cols[6].button("保存", key=f"{date_str}_save"):
            payload = {
                "start_time": start if start else None,
                "end_time": end if end else None,
                "break_minutes": break_m,
                "interruptions": serialize_interruptions(inter_list),
                "side_job_minutes": side_job
            }
            res = requests.post(f"{API_URL}/attendance/{date_str}", json=payload)

            if res.status_code == 200:
                st.success(f"{date_str} を保存しました")
            else:
                st.error(f"保存に失敗: {res.text}")