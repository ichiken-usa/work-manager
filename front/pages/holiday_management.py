import streamlit as st
from datetime import date, datetime
import requests
from typing import List, Dict

API_URL = "http://back:8000/api"

st.title("🎌 祝日管理")

# -------------------------------
# 1. 対象日付で祝日を登録
# -------------------------------
st.subheader("📅 祝日を登録")

selected_date = st.date_input("対象日付を選択", value=date.today())
holiday_name = st.text_input("祝日の名前を入力", value="")

if st.button("祝日を登録"):
    if not holiday_name.strip():
        st.error("祝日の名前を入力してください。")
    else:
        payload = {"date": selected_date.isoformat(), "name": holiday_name}
        try:
            res = requests.post(f"{API_URL}/holidays/", json=payload)
            if res.status_code == 200:
                st.success(f"祝日 '{holiday_name}' を登録しました。")
            elif res.status_code == 400:
                st.error("既に登録されている祝日です。")
            else:
                st.error(f"登録に失敗しました: {res.text}")
        except Exception as e:
            st.error(f"登録時にエラーが発生しました: {e}")

st.markdown("---")

# -------------------------------
# 2. 対象月の祝日一覧を表示
# -------------------------------
st.subheader("📋 対象月の祝日一覧")

month_str = selected_date.strftime("%Y-%m")

def fetch_holidays_by_month(year_month: str) -> List[Dict]:
    try:
        res = requests.get(f"{API_URL}/holidays/{year_month}")
        if res.status_code == 200:
            return res.json()
        else:
            st.error(f"祝日一覧の取得に失敗しました: {res.text}")
            return []
    except Exception as e:
        st.error(f"祝日一覧の取得時にエラーが発生しました: {e}")
        return []

holidays = fetch_holidays_by_month(month_str)

if holidays:
    st.table([{"日付": h["date"], "名前": h["name"]} for h in holidays])
else:
    st.info("この月には祝日が登録されていません。")

# -------------------------------
# 3. 祝日を編集して更新
# -------------------------------
# 祝日を編集して更新
st.subheader("✏️ 祝日を編集")

if holidays:
    holiday_to_edit = st.selectbox("編集する祝日を選択", options=holidays, format_func=lambda h: f"{h['date']} - {h['name']}")
    new_name = st.text_input("新しい祝日の名前を入力", value=holiday_to_edit["name"])
    if st.button("祝日を更新"):
        if not new_name.strip():
            st.error("祝日の名前を入力してください。")
        else:
            # date フィールドを含めた payload を作成
            payload = {
                "date": holiday_to_edit["date"],  # 必須フィールドとして date を追加
                "name": new_name
            }
            try:
                res = requests.put(f"{API_URL}/holidays/{holiday_to_edit['date']}", json=payload)
                if res.status_code == 200:
                    #st.success(f"祝日 '{holiday_to_edit['date']}' を '{new_name}' に更新しました。")
                    st.rerun()  
                else:
                    st.error(f"更新に失敗しました: {res.text}")
            except Exception as e:
                st.error(f"更新時にエラーが発生しました: {e}")

# -------------------------------
# 4. 祝日を削除
# -------------------------------
st.subheader("🗑️ 祝日を削除")

if holidays:
    holiday_to_delete = st.selectbox("削除する祝日を選択", options=holidays, format_func=lambda h: f"{h['date']} - {h['name']}")
    if st.button("祝日を削除"):
        try:
            res = requests.delete(f"{API_URL}/holidays/{holiday_to_delete['date']}")
            if res.status_code == 200:
                st.success(f"祝日 '{holiday_to_delete['name']}' を削除しました。")
                st.experimental_rerun()
            else:
                st.error(f"削除に失敗しました: {res.text}")
        except Exception as e:
            st.error(f"削除時にエラーが発生しました: {e}")

