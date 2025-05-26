import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import date, datetime
from modules.attendance_utils import aggregate_attendance
from modules.api_client import fetch_monthly_summary, fetch_holidays

API_URL = "http://back:8000/api"

st.title("📊 勤怠ダッシュボード")

# --- 当月の予測勤務時間と実績勤務時間の推移グラフ ---
st.subheader("📈 当月の勤務時間推移")

# 対象月を選択（初期値：今月）
today = date.today()
default_month = date(today.year, today.month, 1)
selected_month = st.date_input("対象月を選択", value=default_month)
month_str = selected_month.strftime("%Y-%m")


# 日毎の集計データを取得
daily_data = fetch_monthly_summary(month_str)
# 祝日データの取得
holidays = fetch_holidays(month_str)

import calendar

# グラフデータの作成
if daily_data:
    # 実績データを日付順に並べる
    daily_records = sorted(daily_data, key=lambda x: x["raw"]["date"])  # "raw"キーの"date"でソート
    actual_hours_dict = {record["raw"]["date"]: record["summary"]["actual_work_hours"] for record in daily_records}

    # 月末の日付を計算
    year, month = map(int, month_str.split("-"))
    _, last_day = calendar.monthrange(year, month)
    all_dates = pd.date_range(start=f"{year}-{month:02d}-01", end=f"{year}-{month:02d}-{last_day}")

    # 実績勤務時間を全日付に対応する形で構築
    actual_hours = []
    for date_obj in all_dates:
        date_str = date_obj.strftime("%Y-%m-%d")
        actual_hours.append(actual_hours_dict.get(date_str, 0))  # 登録されていない日は0

    # 土日と祝日を除外して予測勤務時間を計算
    daily_forecast_hours = []
    for date_obj in all_dates:
        date_str = date_obj.strftime("%Y-%m-%d")
        if date_str in actual_hours_dict and actual_hours_dict[date_str] > 0:
            # 実績データがある場合はその実績勤務時間を使用
            daily_forecast_hours.append(actual_hours_dict[date_str])
        elif date_obj.weekday() < 5 and date_str not in holidays:  # 平日かつ祝日でない場合
            daily_forecast_hours.append(8)  # 未登録日は1日8時間の予測
        else:
            daily_forecast_hours.append(0)  # 土日または祝日は0時間

    # 実績データを累積計算
    cumulative_actual_hours = pd.Series(actual_hours).cumsum()

    # 予測勤務時間を累積計算
    cumulative_forecast_hours = pd.Series(daily_forecast_hours).cumsum()

    # データフレーム作成
    df = pd.DataFrame({
        "日付": all_dates.strftime("%Y-%m-%d"),
        "予測勤務時間（累積）": cumulative_forecast_hours,
        "実績勤務時間（累積）": cumulative_actual_hours
    })

import plotly.graph_objects as go

# グラフ描画
fig = px.line(
    df,
    x="日付",
    y=["実績勤務時間（累積）", "予測勤務時間（累積）"],
    labels={"value": "勤務時間（時間）", "variable": "種類"},
    title="当月の勤務時間推移"
)

# 閾値の横棒を追加
fig.add_shape(
    type="line",
    x0=df["日付"].iloc[0],  # グラフの最初の日付
    x1=df["日付"].iloc[-1],  # グラフの最後の日付
    y0=140,  # 閾値の160時間
    y1=140,
    line=dict(color="gray", dash="dash"),  # 赤色の破線
)

fig.add_shape(
    type="line",
    x0=df["日付"].iloc[0],  # グラフの最初の日付
    x1=df["日付"].iloc[-1],  # グラフの最後の日付
    y0=180,  # 閾値の190時間
    y1=180,
    line=dict(color="gray", dash="dash"),  # 青色の破線
)



# グラフを表示
st.plotly_chart(fig, use_container_width=True)