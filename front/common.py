from datetime import datetime, time, date
from typing import Any, Dict, List, Optional
import requests
import streamlit as st

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