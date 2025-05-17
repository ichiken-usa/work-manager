import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import date

API_URL = "http://back:8000/api"

st.title("📊 勤怠ダッシュボード")

# -------------------------------
# 1. 直近12ヶ月の月次サマリー
# -------------------------------
st.subheader("📅 月別 勤務日数 & 勤務時間")

@st.cache_data
def fetch_monthly_summary():
    try:
        res = requests.get(f"{API_URL}/attendance/summary/12months")
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"取得失敗: {e}")
    return []

monthly_data = fetch_monthly_summary()

if monthly_data:
    df_month = pd.DataFrame(monthly_data)
    df_month["month"] = pd.to_datetime(df_month["month"])
    fig1 = px.bar(df_month, x="month", y=["working_days", "total_work_minutes"],
                  labels={"value": "件数", "month": "月"},
                  title="月別 勤務日数（左軸）・勤務時間（分・右軸）")
    st.plotly_chart(fig1, use_container_width=True)
else:
    st.warning("月次データがありません。")

# -------------------------------
# 2. 当月の日別勤務時間グラフ
# -------------------------------
st.subheader("📈 今月の日別 勤務時間")

@st.cache_data
def fetch_daily_summary(month_str):
    try:
        res = requests.get(f"{API_URL}/attendance/summary/daily/{month_str}")
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"取得失敗: {e}")
    return []

today = date.today()
month_str = today.strftime("%Y-%m")
daily_data = fetch_daily_summary(month_str)

if daily_data:
    df_daily = pd.DataFrame(daily_data)
    df_daily["date"] = pd.to_datetime(df_daily["date"])
    fig2 = px.line(df_daily, x="date", y="work_minutes", title=f"{month_str} の日別勤務時間（分）",
                   markers=True)
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.warning("日別データがありません。")
