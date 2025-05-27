import requests
from datetime import datetime, time, date
from typing import Any, Dict, List, Optional
import streamlit as st
from settings import API_URL


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
def fetch_monthly_attendance(month_str):
    try:
        res = requests.get(f"{API_URL}/attendance/month/{month_str}")
        if res.status_code == 200:
            print(f'{API_URL}/attendance/month/{month_str} : {res.json()}')
            return res.json()
    except Exception as e:
        st.error(f"取得失敗: {e}")
    return []

# デイリーのサマリーデータを取得
def fetch_daily_summary(record_date: date) -> Optional[Dict[str, Any]]:
    """
    指定した日付の勤怠データおよび集計データをAPIから取得する。

    Args:
        record_date (date): 取得対象日付

    Returns:
        dict or None: 勤怠データと集計データ（存在しない場合は空dict、失敗時はNone）
    """
    try:
        res = requests.get(f"{API_URL}/attendance/summary/daily/{record_date.isoformat()}")
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
    
# 1ヶ月の集計データを取得する
def fetch_monthly_summary(year_month: str) -> Optional[List[Dict[str, Any]]]:
    """
    指定した年月の勤怠データおよび集計データをAPIから取得する。

    Args:
        year_month (str): 取得対象年月（YYYY-MM形式）

    Returns:
        list or None: 勤怠データと集計データのリスト（失敗時はNone）
    """
    try:
        res = requests.get(f"{API_URL}/attendance/summary/monthly/{year_month}")
        if res.status_code == 200:
            return res.json()
        else:
            st.warning(f"データ取得失敗: {res.status_code}")
            return None
    except Exception as e:
        st.error(f"取得失敗: {e}")
        return None
    

API_URL = "http://back:8000/api"

@st.cache_data
def fetch_forecast_data(year_month):
    try:
        res = requests.get(f"{API_URL}/attendance/forecast/{year_month}")
        if res.status_code == 200:
            return res.json()
        else:
            st.error(f"予測データの取得に失敗しました: {res.text}")
            return None
    except Exception as e:
        st.error(f"予測データの取得時にエラーが発生しました: {e}")
        return None

@st.cache_data
def fetch_daily_attendance(year_month):
    try:
        res = requests.get(f"{API_URL}/attendance/month/{year_month}")
        if res.status_code == 200:
            return res.json()
        else:
            st.error(f"日毎の勤怠データの取得に失敗しました: {res.text}")
            return None
    except Exception as e:
        st.error(f"日毎の勤怠データの取得時にエラーが発生しました: {e}")
        return None

@st.cache_data
def fetch_holidays(year_month):
    try:
        res = requests.get(f"{API_URL}/holidays/{year_month}")
        if res.status_code == 200:
            return [holiday["date"] for holiday in res.json()]  # 祝日の日付リストを取得
        else:
            st.error(f"祝日データの取得に失敗しました: {res.text}")
            return []
    except Exception as e:
        st.error(f"祝日データの取得時にエラーが発生しました: {e}")
        return []
    
@st.cache_data
def fetch_aggregate_attendance(year_month: str) -> Dict[str, float]:
    """
    勤怠データのリストから集計情報を計算する。

    Args:
        records (list): 勤怠データのリスト

    Returns:
        dict: 集計結果（勤務日数、総勤務時間、実働時間など）
    """
    try:
        res = requests.get(f'{API_URL}/attendance/summary/monthly-agg/{year_month}')
        if res.status_code == 200:
            return res.json()
        else:
            st.warning(f"データ取得失敗: {res.status_code}")
            return None
    except Exception as e:
        st.error(f"取得失敗: {e}")
        return None