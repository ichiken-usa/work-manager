import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime
from modules.graph import create_work_hours_graph, prepare_work_hours_graph_data, create_daily_attendance_chart
from modules.api_client import fetch_monthly_summary, fetch_holidays, fetch_aggregate_attendance, fetch_forecast_data

st.title("📊 勤怠ダッシュボード")


st.markdown("## 月集計")

# 対象月を選択（初期値：今月）
today = date.today()
default_month = date(today.year, today.month, 1)
selected_month = st.date_input("対象月を選択", value=default_month)
month_str = selected_month.strftime("%Y-%m")

# ---------------------------------- 
# 集計
# ----------------------------------
agg = fetch_aggregate_attendance(month_str)
if agg is None:
    st.error("集計データの取得に失敗しました。")
else:
    st.table({
        "項目": [
            "総日数:入力のある全日数",
            "総勤務時間：勤務合計と副業合計の総合計", 
            "勤務日数：勤務時間登録がある日数",
            "勤務合計：開始と終了からのみ算出した時間", 
            "実働時間：勤務合計から休憩と中断を引いた時間",
            "休憩合計：休憩時間の合計", 
            "中断合計：中断時間の合計", 
            "副業合計：副業時間の合計",
        ],
        "値": [
            f"{agg['gross_days']} 日",
            f"{agg['gross_total_hours']:.2f} h",
            f"{agg['work_days']} 日",
            f"{agg['work_total_hours']:.2f} h",
            f"{agg['actual_work_hours']:.2f} h",
            f"{agg['break_total_hours']:.2f} h",
            f"{agg['interrupt_total_hours']:.2f} h",
            f"{agg['side_job_total_hours']:.2f} h",
        ]
    })

# ------------------------------ 
# 当月の予測勤務時間と実績勤務時間の推移グラフ 
# ------------------------------
st.markdown(f"### 予測と実績推移")
# 予測勤務時間データを取得して表にする
forecast_data = fetch_forecast_data(month_str)
if forecast_data is None:
    st.error("予測勤務時間の取得に失敗しました。")
else:
    # forecast_data をデータフレームに変換して表示
    st.table(
        {
            "項目": [
                "登録済み勤務時間",
                "予測勤務時間",
                "未登録日数",
                "登録休日数",
            ],
            "値": [
                f"{forecast_data['registered_work_hours']} h",
                f"{forecast_data['predicted_work_hours']} h",
                f"{forecast_data['unregistered_days']} 日",
                f"{forecast_data['holiday_days']} 日",
            ],
        }
    )

# 日毎の集計データを取得
daily_data = fetch_monthly_summary(month_str)
# 祝日データの取得
holidays = fetch_holidays(month_str)

# グラフデータの作成
if daily_data:
    df = prepare_work_hours_graph_data(daily_data, month_str, holidays)

    # グラフを表示
    fig = create_work_hours_graph(df)
    st.plotly_chart(fig, use_container_width=True)


# ----------------------------------
# 1ヶ月の日々の勤怠データの積み重ね棒グラフ
# ----------------------------------
# 日毎の勤怠データを取得
daily_attendance_data = fetch_monthly_summary(month_str)
# グラフ作成して表示
if daily_attendance_data is None:
    st.error("日毎の勤怠データの取得に失敗しました。")
else:
    fig = create_daily_attendance_chart(daily_attendance_data)
    st.plotly_chart(fig, use_container_width=True)