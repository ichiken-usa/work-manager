# セッション管理系

import streamlit as st
from typing import List, Dict, Any

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
