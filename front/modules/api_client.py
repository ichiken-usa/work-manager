import requests
from datetime import datetime, time, date
from typing import Any, Dict, List, Optional
import streamlit as st
from settings import API_URL

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

