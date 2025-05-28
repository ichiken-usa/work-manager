import pandas as pd
import plotly.express as px
import calendar
import plotly.graph_objects as go


def prepare_work_hours_graph_data(daily_data, month_str, holidays):
    """
    グラフ描画用のデータを準備する関数

    Args:
        daily_data (list): 日毎の勤怠データ
        month_str (str): 対象月（YYYY-MM形式）
        holidays (list): 祝日の日付リスト

    Returns:
        pd.DataFrame: グラフ描画用のデータフレーム
    """
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

    return df

def create_work_hours_graph(df: pd.DataFrame, threshold1: float = 140, threshold2: float = 180):
    """
    勤務時間推移と予測のグラフを作成する関数

    Args:
        df (pd.DataFrame): グラフ描画用のデータフレーム
        threshold1 (float): 閾値1（デフォルト140時間）
        threshold2 (float): 閾値2（デフォルト180時間）

    Returns:
        plotly.graph_objects.Figure: 作成されたグラフオブジェクト
    """
    # グラフ描画
    fig = px.line(
        df,
        x="日付",
        y=["予測勤務時間（累積）","実績勤務時間（累積）"],
        labels={"variable": "種類", "value": "勤務時間（時間）"},
    )


    # 予測勤務時間のスタイルを設定（水色の点線）
    fig.data[0].update(line=dict(color="lightblue", width=3, dash="dot"), name="予測勤務時間（累積）")
    # 実績勤務時間のスタイルを設定（青色の実線）
    fig.data[1].update(line=dict(color="blue", width=3), name="実績勤務時間（累積）")

    # 閾値2（上限）を凡例に追加
    fig.add_trace(
        go.Scatter(
            x=[df["日付"].iloc[0], df["日付"].iloc[-1]],
            y=[threshold2, threshold2],
            mode="lines",
            line=dict(color="gray", dash="dash", width=1),
            name="上限（180時間）"
        )
    )
    
    # 閾値1（下限）を凡例に追加
    fig.add_trace(
        go.Scatter(
            x=[df["日付"].iloc[0], df["日付"].iloc[-1]],
            y=[threshold1, threshold1],
            mode="lines",
            line=dict(color="gray", dash="dash", width=1),
            name="下限（140時間）"
        )
    )



    # レイアウト調整
    fig.update_layout(
        title="勤務実績推移と予測",
        xaxis_title="日付",
        yaxis_title="勤務時間（時間）",
        legend_title="種類",
        legend=dict(yanchor="top", y=1, xanchor="left", x=0),
    )

    return fig

def create_daily_attendance_chart(daily_attendance_data):
    """
    日毎の勤怠データを積み上げ棒グラフとして表示する関数。

    Parameters:
        daily_attendance_data (list): 日毎の勤怠データのリスト。
    """

    # データを整形
    data = []
    for record in daily_attendance_data:
        summary = record["summary"]
        data.append({
            "date": record["raw"]["date"],
            "実働時間": summary["actual_work_hours"],
            "休憩時間": summary["break_hours"],
            "中断時間": summary["interrupt_hours"],
            "副業時間": summary["side_job_hours"]
        })

    # DataFrameに変換
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])  # 日付をdatetime型に変換

    # グラフを作成
    fig = px.bar(
        df,
        x="date",
        y=["実働時間", "休憩時間", "中断時間", "副業時間"],
        title="時間内訳積み上げ棒グラフ",
        labels={"value": "時間", "variable": "項目", "date": "日付"},
        barmode="stack"  # 積み上げ棒グラフ
    )
    fig.update_layout(xaxis_title="日付", yaxis_title="時間 (h)")
    return fig
